import time
import asyncio
from threading import Thread
import redis

def get_redis():
    connection_pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
    return redis.Redis(connection_pool=connection_pool)

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

async def async_work(x):
    print('Waiting ', x)
    await asyncio.sleep(x)
    print('Done ', x)

if __name__ == '__main__':
    new_loop = asyncio.new_event_loop()
    t = Thread(target=start_loop, args=(new_loop,))
    t.setDaemon(True) # new thread ends with the main thread
    t.start()
    rcon = get_redis()
    try:
        while True:
            _, task = rcon.brpop("queue") # read input by "lpush queue 2 5 3 1"
            asyncio.run_coroutine_threadsafe(async_work(int(task)), new_loop)
    except Exception as e:
        print('error', e)
        new_loop.stop()
    finally:
        pass