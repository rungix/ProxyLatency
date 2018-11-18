from datetime import datetime, timedelta
from pymongo import MongoClient


class MongoIPLatency:
    """
    Wrapper around MongoDB to cache IP-related Latencies.

    >>> cache = MongoIPLatency()
    >>> cache.clear()
    >>> ip = '8.8.8.8'
    >>> result = {'ip': '...'}
    >>> cache[ip] = result
    >>> cache[ip]['Peer_IP'] == result['Peer_IP']
    True
    >>> cache = MongoIPLatency(expires=timedelta())
    >>> cache[ip] = result
    >>> # every 60 seconds is purged
    >>>   http://docs.mongodb.org/manual/core/index-ttl/
    >>> import time; time.sleep(60)
    """

    def __init__(self, collection="iplatency", username='admin', password='passwd',
                client=None, expires=timedelta(days=720)):
        """
        client: mongo database client
        expires: timedelta of amount of time
                 before a cache entry is considered expired
        """
        # if a client object is not passed
        # then try connecting to mongodb at the default localhost port
        self.client = MongoClient('localhost', 27017, connect=False, username=username, password=password) \
            if client is None else client
        # create collection to store measured IPs,
        # which is the equivalent of a table in a relational database
        self.db = self.client.CDNLatency
        self.collection = self.db[collection]
        self.collection.create_index('timestamp',
                                     expireAfterSeconds=expires.total_seconds())

    def __contains__(self, ip):
        try:
            self[ip]
        except KeyError:
            return False
        else:
            return True

    def __getitem__(self, ip):
        """Load value at this IP
        """
        record = self.collection.find_one({'_id': ip})
        if record:
            return record['result']
        else:
            raise KeyError(ip + ' does not exist')

    def __setitem__(self, ip, result):
        """Save value for this IP
        """
        record = {'result': result, 'timestamp': datetime.utcnow()}
        self.collection.update({'_id': ip}, {'$set': record}, upsert=True)

    def clear(self):
        self.collection.drop()
