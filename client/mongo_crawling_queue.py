from datetime import datetime, timedelta
from pymongo import MongoClient, errors


class MongoCrawlingQueue:
    """
    >>> timeout = 1
    >>> q = MongoQueue(timeout=timeout)
    >>> q.clear() # ensure empty queue
    >>> q.push(ip) # add test IP
    >>> q.peek() == q.pop() == ip # pop back this IP
    True
    >>> q.repair() # immediate repair will do nothin
    >>> q.pop() # another pop should be empty
    >>> q.peek()
    >>> import time; time.sleep(timeout) # wait for timeout
    >>> q.repair() # now repair will release IP
    Released: test
    >>> q.pop() == ip # pop URL again
    True
    >>> bool(q) # queue is still active while outstanding
    True
    >>> q.complete(ip) # complete this IP
    >>> bool(q) # queue is not complete
    False
    """

    # possible states of a crawl
    OUTSTANDING, PROCESSING, COMPLETE = range(3)

    def __init__(self, collection="ingress_ip", username='admin', password='passwd',
                 client=None,
                 timeout=300):
        """
        host: the host to connect to MongoDB
        port: the port to connect to MongoDB
        timeout: the number of seconds to allow for a timeout
        """
        self.client = MongoClient(connect=False, username=username, password=password) \
            if client is None else client
        self.db = self.client.CDNLatency
        print("collection_name %s" % collection)
        self.collection = self.db[collection]
        self.timeout = timeout

    def __nonzero__(self):
        """Returns True if there are more jobs to process
        """
        record = self.db.crawling_queue.find_one(
            {'status': {'$ne': self.COMPLETE}}
        )
        return True if record else False

    def push(self, ip):
        """Add new IP to queue if does not exist
        """
        try:
            self.collection.insert({'_id': ip,
                                    'status': self.OUTSTANDING})
        except errors.DuplicateKeyError as e:
            pass  # this is already in the queue

    def pop(self):
        """Get an outstanding URL from the queue and set its status to processing.
        If the queue is empty a KeyError exception is raised.
        """
        record = self.collection.find_and_modify(
            query={'status': self.OUTSTANDING},
            update={'$set': {'status': self.PROCESSING,
                             'timestamp': datetime.now()}}
        )
        if record:
            return record['_id']
        else:
            self.repair()
            raise KeyError()

    def peek(self):
        record = self.collection.find_one({'status': self.OUTSTANDING})
        if record:
            return record['_id']

    def complete(self, ip):
        self.collection.update({'_id': ip},
                               {'$set': {'status': self.COMPLETE}})

    def repair(self):
        """Release stalled jobs
        """
        record = self.collection.find_and_modify(
            query={
                'timestamp': {'$lt': datetime.now() -
                              timedelta(seconds=self.timeout)},
                'status': {'$ne': self.COMPLETE}
            },
            update={'$set': {'status': self.OUTSTANDING}}
        )
        if record:
            print('Released: %s' % (record['_id']))

    def clear(self):
        self.collection.drop()
