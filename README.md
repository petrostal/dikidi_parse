# dikidi_parse

Parse https://dikidi.ru for company names and phone numbers.
Collected data stores in file contacts.txt

Usage:
    Edit scan range in the end of main.py file and run script.

    parser = DikidiParser()
    parser.collect_with_multiprocessing(
        number_from=100000,
        process_count=50,
        process_size=10000,
    )
    parser.merge_results()

It will scan data with range from number_from to process_count*process_size.

Installation:

git clone git@github.com:petrostal/dikidi_parse.git

cd dikidi_parse

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt


