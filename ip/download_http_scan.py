import coloredlogs, logging
import requests
from bs4 import BeautifulSoup
import re
import time
import wget
import argparse


seed_url = "https://scans.io/study/sonar.http"
root_url = "https://censys.io/data/80-http-get-full_ipv4"
root_file = "zgrab-results.json.lz4"


def get_gz_links():

    # create response object
    r = requests.get(seed_url)

    # create beautiful-soup object
    soup = BeautifulSoup(r.content, 'html5lib')

    # find all links on web-page
    links = soup.findAll('a')

    # filter the link sending with .gz
    gz_links = [link['href'] for link in links if link['href'].endswith('gz')]

    return gz_links


def download_gz_newest(gz_links):

    newest_date = time.strptime("2017-03-30", "%Y-%m-%d")

    for link in gz_links:

        '''iterate through all links in gz_links
        and download them one by one'''

        # obtain filename by splitting url and getting
        # last string
        file_name = link.split('/')[-1]
        file_date = re.search(r'(\d+-\d+-\d+)', file_name)
        if file_date is None:
            continue
        print("file: %s, date: %s" % (file_name, str(file_date.group(0))))

        date = time.strptime(file_date.group(0), "%Y-%m-%d")
        if date > newest_date:
            newest_date = date
            newest_link = link

    logging.info("Downloading file: %s, date %s" % (file_name, file_date))
    logging.info("Downloading URL: %s" % newest_link)

    # download started
    downloaded_file = wget.download(newest_link, out="../download/")
    logging.critical("%s downloaded!\n" % downloaded_file)

    return


def download_lz4():
    # Censys reuqire session cookies...
    r = requests.get(root_url)
    print(r)
    soup = BeautifulSoup(r.content, 'html5lib')
    for link in soup.findAll('a'):
        logging.error(link)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
                                     'Download HTTP scaning data from Censys')
    parser.add_argument('-t', '--threads', dest='threads',
                        help='number of threads for downloading',
                        required='True', type=int, default='4')
    parser.add_argument('-f', '--file', dest='file',
                        help='Data source',
                        type=str, default='sonar')

    args = parser.parse_args()
    if args.file == 'sonar':
        
        gz_links = get_gz_links()
        # download the newest *.gz
        download_gz_newest(gz_links)
    else:
        download_lz4()
