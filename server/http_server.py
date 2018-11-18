from aiohttp import web
import json
import aioping
import numpy
import random
import string
import time


async def index_handler(request):
    resp = {}
    host = "Unknown"
    port = 0
    resp['id'] = 'index'
    resp['Origin_Time_Request'] = time.time()
    peername = request.transport.get_extra_info('peername')
    if peername is not None:
        host, port = peername
    resp['Peer_IP'] = str(host)
    resp['Peer_Port'] = str(port)
    resp['HTTP_Client_Headers'] = json.dumps(dict(request.headers))
    resp['Key'] = ''.join([random.choice(string.ascii_letters + string.digits)
                           for n in range(32)])
    resp['Origin_Time_Response'] = time.time()
    return web.Response(text=json.dumps(resp))


def common_response(request, resp):
    host = "Unknown"
    resp['Origin_Time_Request'] = time.time()
    resp['Edge_IP'] = str(request.match_info['edge_ip'])
    peername = request.transport.get_extra_info('peername')
    if peername is not None:
        host, port = peername
    resp['Peer_IP'] = str(host)
    resp['Peer_Port'] = str(port)
    resp['HTTP_Client_Headers'] = json.dumps(dict(request.headers))
    resp['Key'] = ''.join([random.choice(string.ascii_letters + string.digits)
                           for n in range(32)])
    return resp


async def cache_handler(request):
    resp = {}
    resp['id'] = 'Cache'
    resp = common_response(request, resp)
    resp['Origin_Time_Response'] = time.time()
    return web.Response(text=json.dumps(resp))


async def origin_handler(request):
    resp = {}
    resp['id'] = 'Origin'
    resp = common_response(request, resp)
    resp['Origin_Time_Response'] = time.time()
    return web.Response(text=json.dumps(resp))


async def do_ping(ip):
    try:
        delay = await aioping.ping(ip, timeout=1)  # timeout=1s
        #  print("Ping %s in %f s" % (ip, delay))
        return delay
    except TimeoutError:
        print("Ping %s timeout" % ip)


async def ping_handler(request):
    resp = {}
    resp['id'] = 'Ping'
    resp = common_response(request, resp)
    ip = resp['Peer_IP']
    ping_count = int(request.match_info['ping_count'])
    latency = []
    for i in range(ping_count):
        delay = await do_ping(ip)
        if delay is not None:
            latency.append(delay)
    if not latency:
        latency = [0]
    latency = numpy.array(latency)
    result = {}
    result['Mean'] = numpy.mean(latency)
    result['Std'] = numpy.std(latency)
    result['Median'] = numpy.median(latency)
    resp['Egress_Ping'] = result
    print("Ping %s in %f s" % (ip, result['Median']))
    resp['Origin_Time_Response'] = time.time()
    return web.Response(text=json.dumps(resp))


def setup_routes(app):
    app.router.add_get('/', index_handler)
    # app.router.add_get('/{name}/cache/{tail:.*}', cache_handler)
    app.router.add_get('/{edge_ip}/cache.txt', cache_handler)
    app.router.add_get('/{edge_ip}/origin/{tail:.*}', origin_handler)
    app.router.add_get('/{edge_ip}/ping/{ping_count}/{tail:.*}', ping_handler)


app = web.Application()
setup_routes(app)
web.run_app(app, port=80)
