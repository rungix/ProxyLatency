import numpy
import pexpect
import sys


class PingBench:
    """Ping target IP
    Adapted from https://github.com/matthieu-lapeyre/network-benchmark
                        /blob/master/network_test.py
    """
    def __init__(self, ip, interval=1):
        self.ip = ip
        self.interval = interval
        self.ping_cmd = 'ping -i ' + str(self.interval) + ' -w 5 ' + self.ip
        self.process = pexpect.spawn(self.ping_cmd)
        self.process.timeout = 50
        self.process.readline()  # init
        self.latency = []
        self.timeout = 0
        self.print_status = False

    def ping(self, n_sample=10):
        for i in range(n_sample):
            p = str(self.process.readline())
            try:
                ping_time = float(p[p.find('time=') + 5:p.find(' ms')])
                self.latency.append(ping_time / 1000.0)
                if self.print_status:
                    print("Ping: " + str(i + 1) + '/' + str(n_sample) +
                          " --- latency: " + str(ping_time) + 'ms')
            except Exception:
                self.timeout = self.timeout + 1
        self.timeout = self.timeout / float(n_sample)
        self.latency = numpy.array(self.latency)

    def get_results(self):
        result = {}
        if self.latency.size:
            result['mean'] = numpy.mean(self.latency)
            result['std'] = numpy.std(self.latency)
            result['median'] = numpy.median(self.latency)
        return result


if __name__ == '__main__':

    if len(sys.argv) < 3:
        print("usage: python " + sys.argv[0] + ' <ip> <n_sample>')
        sys.exit(1)

    ip = sys.argv[1]
    n_sample = int(sys.argv[2])

    pingbench = PingBench(ip, 0.5)
    pingbench.print_status = True
    pingbench.ping(n_sample)
    print(str(pingbench.get_results()))
