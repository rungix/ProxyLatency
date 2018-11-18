import time
import threading
import multiprocessing
from mongo_crawling_queue import MongoCrawlingQueue
from measure import MeasureLatency
import os

SLEEP_TIME = 1


def threaded_crawler(delay=5, ip_collection_name='ingress_ip',
                     host='www.apple.com',
                     max_threads=10, num_measures=5,
                     username='admin', password='passwd'):
    """Crawl using multiple threads
    """
    # the queue of URL's that still need to be crawled
    crawling_queue = MongoCrawlingQueue(collection=ip_collection_name,  username=username, password=password)
    # crawling_queue.clear()
    latency_collection = ip_collection_name + "_Latency"
    #  M = MeasureLatency(delay=delay, collection=latency_collection,
    #  host=host, num_measures=num_measures)

    def process_queue():
        while True:
            # keep track that are processing url
            try:
                ip = crawling_queue.pop()
                print(">>> Pop IP %s" % ip)
            except KeyError:
                # currently no IPs to process
                print("PID %d: currently no IPs to process,"
                      "thread exiting..." % os.getpid())
                break
            else:
                print("PID %d processes %s" % (os.getpid(), ip))
                M = MeasureLatency(username, password, delay=delay, collection=latency_collection,
                                   host=host, num_measures=num_measures)
                M(ip)
                crawling_queue.complete(ip)
                print("PID %d processed %s" % (os.getpid(), ip))

    # wait for all download threads to finish
    threads = []
    while threads or crawling_queue.peek():
        # print("PID %d len of thread %d" % (os.getpid(), len(threads)))
        for thread in threads:
            if not thread.is_alive():
                threads.remove(thread)
        while len(threads) < max_threads and crawling_queue.peek():
            # can start some more threads
            print("PID %d starts new thread" % os.getpid())
            thread = threading.Thread(target=process_queue)
            # set daemon so main thread can exit when receives ctrl-c
            thread.setDaemon(True)
            thread.start()
            threads.append(thread)
        time.sleep(SLEEP_TIME)
        # print("PID %d sleeping..." % os.getpid())
    print("PID %d exiting..." % os.getpid())


def process_crawler(**kwargs):
    num_cpus = multiprocessing.cpu_count()
    print('>>>>> Starting {%d} processes' % (num_cpus))
    processes = []
    for i in range(num_cpus):
        p = multiprocessing.Process(target=threaded_crawler, kwargs=kwargs)
        p.start()
        processes.append(p)
    # wait for processes to complete
    for p in processes:
        p.join()
