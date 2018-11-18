import aioping
import asyncio


async def do_ping(ip):
    try:
        delay = await aioping.ping(ip, timeout=1)  # timeout=1s
        print("Ping %s in %d ms" % (ip, delay))
        return delay
    except TimeoutError:
        print("Ping %s timeout" % ip)


async def ping():
    for i in range(8):
        delay = await do_ping('8.8.8.8')
        if delay is not None:
            print(delay)


if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(ping())
    event_loop.close()
