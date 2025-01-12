import aiohttp
import asyncio
import base64
import os
import requests
from bs4 import BeautifulSoup
from multiprocessing import Process


class DikidiParser:
    """
    Parser for dikidi.ru
    Class can parse and coolect data such as company name and phone numbers
    from dikidi.ru. You can use multiprocessing or asyncio/ aiohttp. 
    The last one is work too bad because it obtain ban from CloudFlare.
    By default data stores in file contacs.txt
    """
    LIMIT = 100
    BASE_URL = (
        f'https://dikidi.ru/ru/ajax/catalog/filter/?limit={LIMIT}&offset='
    )
    SUFFIX_URL = '&more=1&category=&query=&sort=0&address=&show=0'
    COMPANY_URL = 'https://dikidi.ru/ru/profile/'

    def _collect_ids_by_offset(self, offset: int = LIMIT) -> list[str]:
        """
        Parse one catalog page with pagination data offset and limit.
        Collect company ids from this page.
        """
        url = f'{self.BASE_URL}{offset}'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
        except Exception as e:
            print(e)
            return
        try:
            if not data:
                return
            data = data.get('script', [])[0].get('html')
        except Exception as e:
            print(e, response.text)
            return
        soup = BeautifulSoup(data, 'lxml')
        raw_data = soup.find_all('div', attrs={'class': 'favorite-status'})
        result = [
            item.get('data-href', '').split('/')[-2] for item in raw_data
        ]
        if len(result) == 0:
            return
        return result

    def collect_ids(self) -> list[str]:
        """
        Collect company ids from catalog.
        """
        result = []
        offset = 0
        while ids := self._collect_ids_by_offset(offset):
            result.extend(ids)
            offset += self.LIMIT
        return result

    def get_phone_by_company_id(self, id: str) -> str:
        """
        Collect company name and phone number by company id.
        """
        url = f'{self.COMPANY_URL}{id}'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.text
        except Exception:
            return
        soup = BeautifulSoup(data, 'lxml')
        raw_phone = soup.find(
            'div', attrs={'class': 'phones collapsed'}
        ).attrs['data-list']
        phone = base64.b64decode(raw_phone).decode()
        salon_name = soup.find('h1', attrs={'class': 'title'}).text
        salon_address = soup.find('div', attrs={'class': 'address'}).text
        return f'{salon_name} :: {salon_address} :: {phone}'

    def collect_phones(
        self, company_ids: list = [], filename: str = 'contacts.txt'
    ) -> list:
        """
        Collect company name and phone number by each company id
        in list. List can be obtained by collect_ids method.
        Also list can be just range of numbers.
        Data stores in file contacts.txt by default.
        """
        with open(filename, 'w') as f:
            for id in company_ids:
                try:
                    contact = self.get_phone_by_company_id(id)
                    f.write(f'{contact}\n')
                    print(f'{id} - {contact}')
                except Exception:
                    pass

    async def asyn_get_phones(self, company_ids: list = []):
        """
        Async method for collect_phones. Not work properly
        because of CloudFlare ban.
        """
        async with aiohttp.ClientSession() as session:
            tasks = []
            for id in company_ids:
                url = f'{self.COMPANY_URL}{id}'
                cookies = {}
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
                    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Referer': url,
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                    'Priority': 'u=0, i',
                }
                tasks.append(
                    asyncio.create_task(
                        session.request(
                            method='GET',
                            url=url,
                            cookies=cookies,
                            headers=headers,
                        )
                    )
                )
            responses = await asyncio.gather(*tasks)
            with open('contacts.txt', 'a') as f:
                for response in responses:
                    if response.status == 200:
                        data = await response.text()
                        soup = BeautifulSoup(data, 'lxml')
                        raw_phone = soup.find(
                            'div', attrs={'class': 'phones collapsed'}
                        ).attrs['data-list']
                        phone = base64.b64decode(raw_phone).decode()
                        salon_name = soup.find(
                            'h1', attrs={'class': 'title'}
                        ).text
                        salon_address = soup.find(
                            'div', attrs={'class': 'address'}
                        ).text
                        print(
                            (
                                f'{response.url} :: {salon_name} :: '
                                f'{salon_address} :: {phone}'
                            )
                        )
                        f.write(
                            (
                                f'{response.url} :: {salon_name} :: '
                                f'{salon_address} :: {phone}\n'
                            )
                        )

    def collect_with_multiprocessing(
        self,
        number_from: int,
        process_count: int = 10,
        process_size: int = 10000,
    ) -> None:
        """
        Method for collect_phones by multiprocessing. It create
        process_count number of processes. Each process collect
        data from process_size range of numbers. Data will be scanned
        from range(number_from, number_from + process_count * process_size).
        Each process write data to file with name contacts_{start}_{end}.txt.
        """
        processes = []
        for i in range(process_count):
            start = number_from + i * process_size
            end = start + process_size - 1
            filename: str = f'contacts_{start}_{end}.txt'
            processes.append(
                Process(
                    target=self.collect_phones,
                    args=(range(start, end), filename),
                    daemon=True,
                )
            )
        for i in range(process_count):
            processes[i].start()
        for i in range(process_count):
            processes[i].join()

    def collect_with_asyncio(
        self,
        from_number: int = 1,
        to_number: int = 100000
    ) -> None:
        """
        Simple asyncio request for collect_phones with range.
        """
        asyncio.run(self.asyn_get_phones(range(from_number, to_number)))

    def merge_results(
        self,
        base_filename: str = 'contacts',
        remove_files: bool = False
    ) -> None:
        """
        Merge all files with contacts data into 1 file contacts.txt.
        """
        files_list = os.listdir()
        with open(f'{base_filename}.txt', 'w') as f:
            for file in files_list:
                if file.startswith(base_filename) and file.endswith('.txt'):
                    with open(file, 'r') as file:
                        f.write(file.read())
                    if remove_files:
                        os.remove(file)


if __name__ == '__main__':
    parser = DikidiParser()
    parser.collect_with_multiprocessing(
        number_from=100000,
        process_count=50,
        process_size=10000,
    )
    parser.merge_results()
