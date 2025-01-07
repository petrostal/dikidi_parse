import base64
import requests
from bs4 import BeautifulSoup

LIMIT = 100
BASE_URL = f'https://dikidi.ru/ru/ajax/catalog/filter/?limit={LIMIT}&offset='
SUFFIX_URL = '&more=1&category=&query=&sort=0&address=&show=0'
COMPANY_URL = 'https://dikidi.ru/ru/profile/'


def collect_ids_by_offset(offset: int = LIMIT) -> list:
    url = f'{BASE_URL}{offset}'
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
    result = [item.get('data-href', '').split('/')[-2] for item in raw_data]
    if len(result) == 0:
        return
    return result


def collect_ids() -> list:
    result = []
    offset = 0
    while ids := collect_ids_by_offset(offset):
        result.extend(ids)
        offset += LIMIT
    return result


def get_phone_by_company_id(id: str) -> str:
    url = f'{COMPANY_URL}{id}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.text
    except Exception as e:
        print(e)
        return
    soup = BeautifulSoup(data, 'lxml')
    raw_phone = soup.find('div', attrs={'class': 'phones collapsed'}).attrs['data-list']
    phone = base64.b64decode(raw_phone).decode()
    salon_name = soup.find('h1', attrs={'class': 'title'}).text
    salon_address = soup.find('div', attrs={'class': 'address'}).text
    return f'{salon_name} :: {salon_address} :: {phone}'


def collect_phones(company_ids: list = []) -> list:
    with open('contacts.txt', 'w') as f:
        for id in company_ids:
            try:
                contact = get_phone_by_company_id(id)
                f.write(f'{contact}\n')
                print(f'{id} - {contact}')
            except Exception as e:
                print(e)


if __name__ == '__main__':
    # ids = collect_ids()
    # with open('ids.txt', 'w') as f:
    #     f.write('\n'.join(ids))
    # with open('ids.txt', 'r') as f:
    #     ids = f.read().split('\n')
    # collect_phones(ids)
    collect_phones(range(2050, 2099))
