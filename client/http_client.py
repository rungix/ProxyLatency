import pycurl
import logging
import time
from termcolor import colored
import os
try:
    from io import BytesIO as StringIO
except ImportError:
    from StringIO import StringIO
import json


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')


class HTTPPara:
    """Default Para for HTTP connection
    """
    DEFAULT_HTTPHEADER = ['Host: www.apple.com',
                          'CDN: Akamai']
    DEFAULT_AGENT = 'Latency Measurement Agent'


class HTTPClient:
    """Connect to target edge node
    Send HTTP Get to measure latency
    """

    def __init__(self, http_header=HTTPPara.DEFAULT_HTTPHEADER,
                 timeout=9):
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.VERBOSE, 0)
        self.curl.setopt(pycurl.MAXREDIRS, 0)
        self.curl.setopt(pycurl.CONNECTTIMEOUT, 9)
        self.curl.setopt(pycurl.TIMEOUT, timeout)
        self.curl.setopt(pycurl.ENCODING, 'gzip')
        self.curl.setopt(pycurl.USERAGENT, HTTPPara.DEFAULT_AGENT)
        self.curl.setopt(pycurl.HTTPHEADER, http_header)

    def get(self, url):
        record = {}
        resp = StringIO()
        resp_header = StringIO()
        self.curl.setopt(pycurl.URL, url)
        self.curl.setopt(pycurl.WRITEFUNCTION, resp.write)
        self.curl.setopt(pycurl.HEADERFUNCTION, resp_header.write)
        try:
            client_time = time.time()
            #  print("Begin %s >>> %s" % (url, client_time))
            self.curl.perform()
        except Exception as e:
            logging.info("Pycurl Oops! " + url + ":" + str(e) + " occured.")
            record['HTTP_Error'] = str(e)
            # Treat 'Key'='0123456789' as the error code
            record['Key'] = 'curl'
            return record
        record['DNS_Time'] = \
            self.curl.getinfo(pycurl.NAMELOOKUP_TIME)  # The time in seconds
        # Time from start until remote host or proxy completed.
        record['Connect_Time'] = \
            self.curl.getinfo(pycurl.CONNECT_TIME)
        record['Pretransfer_Time'] = \
            self.curl.getinfo(pycurl.PRETRANSFER_TIME)
        record['Starttransfer_Time'] = \
            self.curl.getinfo(pycurl.STARTTRANSFER_TIME)
        record['HTTP_Response_Header'] = resp_header.getvalue().decode('UTF-8')
        resp_string = resp.getvalue().decode('UTF-8')
        try:
            resp_dict = json.loads(resp_string)
            #  print(resp_dict)
        except Exception as e:
            logging.info("JsonLoad Oops! " + url + ":" + str(e) + " occured.")
            record['HTTP_Error'] = str(e)
            record['HTTP_Response'] = resp_string
            # Use 'Key'as the error code
            record['Key'] = 'json'
            return record
        else:
            record['HTTP_Error'] = 'None'
            record.update(resp_dict)
            # change into relative latency
            # print("End %s <<< Begin %s, End %s:%s" %
            #       (url, client_time, record['Origin_Time_Request'],
            #        record['Origin_Time_Response']))
            record['Origin_Time_Request'] = \
                record['Origin_Time_Request'] - client_time
            record['Origin_Time_Response'] = \
                record['Origin_Time_Response'] - client_time
            print(">>>%s: %s <<< Begin %s, Relative End %s:%s" %
                  (colored(os.getpid(), 'green'), colored(url, 'blue'),
                   client_time, record['Origin_Time_Request'],
                   record['Origin_Time_Response']))
        return record


if __name__ == '__main__':
    http = HTTPClient()
    start_time = time.time()
    results = http.get('www.apple.com')
    print(results)
    end_time = time.time()
    elapsed = end_time - start_time
    print("Start %f, End %d, Elapsed %f" % (start_time, end_time, elapsed))

    start_time = time.time()
    results = http.get('www.apple.com/a.html')
    print(results)
    end_time = time.time()
    elapsed = end_time - start_time
    print("Start %f, End %d, Elapsed %f" % (start_time, end_time, elapsed))

    start_time = time.time()
    print(http.get('www.apple.com/b.html'))
    time.sleep(10)
    end_time = time.time()
    elapsed = end_time - start_time
    print("Start %f, End %d, Elapsed %f" % (start_time, end_time, elapsed))

    print("#" * 10)
    start_time = time.time()
    print(http.get('127.0.0.1/1.2.3.4/cache.txt'))
    end_time = time.time()
    elapsed = end_time - start_time
    print("Start %f, End %d, Elapsed %f" % (start_time, end_time, elapsed))

    start_time = time.time()
    print(http.get('127.0.0.1/1.2.3.4/ping/5/randomstring'))
    end_time = time.time()
    elapsed = end_time - start_time
    print("Start %f, End %d, Elapsed %f" % (start_time, end_time, elapsed))
