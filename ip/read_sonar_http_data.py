import ijson
import sys
from io import StringIO
import base64
import time

DATA_DIR = "../data/inbound/"

def load_json(line):
    Akamai_file = DATA_DIR + "Akamai_inbound_IP_" + \
        time.strftime("%Y%m%d") + ".txt"
    CloudFront_file = DATA_DIR + "CloudFront_inbound_IP_" + \
        time.strftime("%Y%m%d") + ".txt"
    Cloudflare_file = DATA_DIR + "Cloudflare_inbound_IP_" + \
        time.strftime("%Y%m%d") + ".txt"
    Fastly_file = DATA_DIR + "Fastly_inbound_IP_" + \
        time.strftime("%Y%m%d") + ".txt"
    Baidu_file = DATA_DIR + "Baidu_inbound_IP_" + \
        time.strftime("%Y%m%d") + ".txt"
    items = ijson.items(StringIO(line), '')
    for item in items:
        ip = item['ip']
        data = item['data']
        html = base64.b64decode(data)
        if str(html).find('Server: AkamaiGHost') is not -1:
            write_line = ip 
            filename = Akamai_file
        elif str(html).find('Server: CloudFront') is not -1:
            write_line = ip
            filename = CloudFront_file
        elif str(html).find('Server: cloudflare-nginx') is not -1:
            write_line = ip
            filename = Cloudflare_file
        elif str(html).find('<title>Fastly error') is not -1:
            write_line = ip
            filename = Fastly_file
        elif str(html).find('yunjiasu-nginx') is not -1:
            write_line = ip
            filename = Baidu_file
        else:
            continue
        #  print(html)
        file = open(filename, "a")
        file.write(write_line + "\n")
        print(write_line)


for line in sys.stdin:
    load_json(line)
