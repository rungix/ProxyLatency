import random
import time
import numpy
from datetime import datetime
import string
from termcolor import colored
import os
from mongo_iplatency import MongoIPLatency
from http_client import HTTPClient
from ping import PingBench

DEFAULT_DELAY = 5
DEFAULT_HOST = 'www.apple.com'
DEFAULT_COLLECTION = 'iplatency'


class MeasureLatency:

    def __init__(self, username, password,
                 delay=DEFAULT_DELAY,
                 collection=DEFAULT_COLLECTION,
                 host=DEFAULT_HOST,
                 num_measures=3):
        self.throttle = Throttle(delay)
        self.num_measures = num_measures
        self.iplatency_cache = \
            MongoIPLatency(collection=collection,
                           username=username, password=password)
        host_header = "Host: %s" % host
        http_header = [host_header, "Connection: keep-alive"]
        self.http = HTTPClient(http_header=http_header)
        self.records = {}

    def __call__(self, ip):
        self.records = {}
        self.records['Measure_Error'] = ''
        self.measure(ip)
        return

    def measure_ping(self, ip, num_measures=3, interval=0.5):
        pingbench = PingBench(ip, interval)
        pingbench.ping(num_measures)
        self.records['Ingress_Ping'] = pingbench.get_results()

    def measure_http_cache(self, ip, num_measures=3):
        url_cache = 'http://' + ip + '/' + ip + '/cache.txt'
        record = self.http.get(url_cache)
        ingress_latency = []

        if record['HTTP_Error'] != 'None':
            self.records['Measure_Error'] = 'Cache'
            self.records['Measure_Error_Code'] = record['Key']
            self.records['Measure_Error_Msg'] = record['HTTP_Error']
            return

        if record['Key'] in ['curl', 'json']:
            self.records['Measure_Error'] = 'Cache'
            self.records['Measure_Error_Code'] = record['Key']
            self.records['Measure_Error_Msg'] = record['HTTP_Error']
            # nonsense to loop when meet HTTP-Get-error or json-load-error
            # what if error occured in loop 3? Currently not considered.
            return

        key = record['Key']
        for i in range(num_measures):
            record = self.http.get(url_cache)

            if record['Key'] in ['curl', 'json']:
                self.records['Measure_Error'] = 'Cache'
                self.records['Measure_Error_Code'] = record['Key']
                self.records['Measure_Error_Msg'] = record['HTTP_Error']
                # nonsense to loop when meet HTTP-Get-error or json-load-error
                # what if error occured in loop 3? Currently not considered.
                break

            # Cached resources should have the same 'Key'
            if record['Key'] != key:
                break
            record['Ingress_RTT'] = \
                float(record['Starttransfer_Time']) - \
                float(record['Pretransfer_Time'])
            self.records['http_cache_' + str(i)] = record
            ingress_latency.append(float(record['Ingress_RTT']) / 2.0)

        if ingress_latency:
            ingress_latency_array = numpy.array(ingress_latency)
            self.records['Ingress_Latency'] = {}
            self.records['Ingress_Latency']['mean'] = \
                numpy.mean(ingress_latency_array)
            self.records['Ingress_Latency']['median'] = \
                numpy.median(ingress_latency_array)
            self.records['Ingress_Latency']['std'] = \
                numpy.std(ingress_latency_array)

 

    def measure_http_origin(self, ip, num_measures=3):
        request_latency = []
        response_latency = []
        key = ""
        for i in range(num_measures):
            randomstr = ''.join([random.choice(string.ascii_letters +
                                               string.digits) for n in range(16)])
            url_origin = 'http://' + ip + '/' + ip + '/origin/' + \
                randomstr + ".php"
            record = self.http.get(url_origin)

            if record['Key'] in ['curl', 'json']:
                self.records['Measure_Error'] = 'Origin'
                self.records['Measure_Error_Code'] = record['Key']
                self.records['Measure_Error_Msg'] = record['HTTP_Error']
                # nonsense to loop when meet HTTP-Get-error or json-load-error
                # what if error occured in loop 3? Currently not considered.
                break

            # Ignore the cached result
            if key == record['Key']:
                print(">"*80)
                print("Access %s returned cached result, key = %s" %
                      (url_origin, record['key']))
                print("<"*80)
                continue

            # Non-cacheable resources should be different in 'key'
            key = record['Key']

            # to demonstrate path symmetry, request_latency ?= response_latency
            record['Request_Latency'] = \
                record['Origin_Time_Request'] * 1.0 - \
                record['Pretransfer_Time'] * 1.0
            request_latency.append(float(record['Request_Latency']))

            record['Response_Latency'] = \
                record['Starttransfer_Time'] * 1.0 - \
                record['Origin_Time_Response'] * 1.0
            response_latency.append(float(record['Response_Latency']))

            self.records['http_origin_' + str(i)] = record

        if request_latency:
            request_latency_array = numpy.array(request_latency)
            self.records['Request_Latency'] = {}
            self.records['Request_Latency']['mean'] = \
                numpy.mean(request_latency_array)
            self.records['Request_Latency']['median'] = \
                numpy.median(request_latency_array)
            self.records['Request_Latency']['std'] = \
                numpy.std(request_latency_array)


        if response_latency:
            response_latency_array = numpy.array(response_latency)
            self.records['Response_Latency'] = {}
            self.records['Response_Latency']['mean'] = \
                numpy.mean(response_latency_array)
            self.records['Response_Latency']['median'] = \
                numpy.median(response_latency_array)
            self.records['Response_Latency']['std'] = \
                numpy.std(response_latency_array)

                
    def measure(self, ip):
        record = None
        print(">"*30 + ip + ">"*30)
        if self.iplatency_cache:
            try:
                record = self.iplatency_cache[ip]
            except KeyError:
                # IP is not available in iplatency_cache
                pass
            else:
                print('$$$$$$$ %s hits IPLatency cache' % ip)
        if record is None:
            # self.measure_ping(ip, num_measures=self.num_measures)
            self.measure_http_cache(ip, num_measures=self.num_measures)
            if self.records['Measure_Error'] in ['Cache', ]:
                self.iplatency_cache[ip] = self.records
                print("!!!!! PID %s, %s Error %s" %
                      (os.getpid(), colored(ip, 'green'),
                       colored(self.records['Measure_Error_Code'], 'red')))
                return

            self.measure_http_origin(ip, num_measures=self.num_measures)
            self.iplatency_cache[ip] = self.records
        print("<"*30 + ip + "<"*30 + '\n\n')
        return


class Throttle:
    """Throttle downloading by sleeping between requests to same IP
    """

    def __init__(self, delay):
        # amount of delay between downloads for each domain
        self.delay = delay
        # timestamp of when a IP was last accessed
        self.ips = {}

    def wait(self, ip):
        """Delay if have accessed the IP recently
        """
        last_accessed = self.ips.get(ip)
        if self.delay > 0 and last_accessed is not None:
            sleep_secs = self.delay - (datetime.now() - last_accessed).seconds
            if sleep_secs > 0:
                time.sleep(sleep_secs)
        self.ips[ip] = datetime.now()
