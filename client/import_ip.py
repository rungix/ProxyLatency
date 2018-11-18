# -*- coding: utf-8 -*-

from mongo_crawling_queue import MongoCrawlingQueue


class ImportIP:
    def __init__(self, ip_file='cdn_ip.txt', max_ips=0,
                 username='admin', password='pass'):
        self.max_ips = max_ips
        self.ip_file = ip_file
        self.username = username
        self.password= password
        if max_ips == 0:
            try:
                self.max_ips = sum(1 for line in open(self.ip_file))
            except Exception as e:
                print("Read %s error %s" % (self.ip_file, str(e)))

    def invalidIP(self, address):
        parts = address.split(".")
        if len(parts) != 4:
            return True
        for item in parts:
            if not 0 <= int(item) <= 255:
                return True
        return False

    def __call__(self, ip_collection_name):
        self.crawling_queue = MongoCrawlingQueue(ip_collection_name,
                                                 username=self.username, 
                                                 password=self.password)
        self.crawling_queue.clear()
        print("Processing %s for %d IPs" % (self.ip_file, self.max_ips))
        try:
            with open(self.ip_file) as fp:
                line = fp.readline().strip()
                count = 0
                while line:
                    if self.invalidIP(line):
                        print("Bad IP: %s" % line)
                        continue
                    print("%d: Save %s to DB %s" % (count, line,
                                                    ip_collection_name))
                    self.crawling_queue.push(line)
                    count += 1
                    if count == self.max_ips:
                        break
                    line = fp.readline().strip()
        except Exception as e:
            print("Read %s error %s" % (self.ip_file, str(e)))
            return False
        return True
