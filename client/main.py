# -*- coding: utf-8 -*-
import os
from process_crawler import process_crawler
import argparse
import datetime
from import_ip import ImportIP
DB_USER = "user"
DB_PASS = "passwd"


def main(max_threads=8, host='www.apple.com', ipfile='cdn_ip.txt',
         num_measures='3', username=DB_USER, password=DB_PASS, ip_count=5):
    ip_collection_name = \
        os.path.basename(ipfile + "_" +
                         datetime.datetime.now().strftime("%y-%m-%d"))
    import_ip = ImportIP(ip_file=ipfile, max_ips=ip_count,
                         username=username, password=password)
    if not import_ip(ip_collection_name):
        return
    process_crawler(ip_collection_name=ip_collection_name,
                    max_threads=max_threads, host=host,
                    num_measures=num_measures,
                    username=username, password=password)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A Simple Crawler')
    parser.add_argument('-t', '--threads', dest='threads',
                        help='number of threads per processor',
                        required='True', type=int, default='8')
    parser.add_argument('-o', '--host', dest='host',
                        help='Host header that affects CDN routing',
                        required='True', type=str, default='www.apple.com')
    parser.add_argument('-f', '--ipfile', dest='ipfile',
                        help='IP file to be stored in mongo for crwaling',
                        required='True', type=str, default='cdn_ip.txt')
    parser.add_argument('-n', '--num', dest='num',
                        help='Number of Get within each HTTP Session',
                        type=int, default='3')
    parser.add_argument('-c', '--count', dest='count',
                        help='Number of IPs to process',
                        type=int, default='0')
    parser.add_argument('-u', '--user', dest='username',
                        help='User name of the mongodb',
                        type=str, default=DB_USER)
    parser.add_argument('-p', '--passwd', dest='password',
                        help='Password of the mongodb',
                        type=str, default=DB_PASS)
    args = parser.parse_args()

    main(args.threads, args.host, args.ipfile, args.num,
         args.username, args.password, args.count)
