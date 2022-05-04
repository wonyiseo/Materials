# from QueueServer.redisqueue import RedisQueueWorker
import threading

from redisqueue import RedisQueueWorker

QUEUE_PASS = "queue1234"
SERVER_IP = "3.35.238.103"
SERVER_PORT = 6379
DB = 0

q = RedisQueueWorker(event_q_name="queue1" , worker_q_name="queue11" , host=SERVER_IP , port=SERVER_PORT , db=DB ,
                     password=QUEUE_PASS)
import time


class Functor(object):
    def __init__(self):
        pass

    @staticmethod
    def print_queue():
        while True:
            time.sleep(1)
            print(time.strftime("%Y-%m-%d %H:%M:%S") , q.get_rqueue().llen("queue1"))


if __name__ == '__main__':
    thread_item = threading.Thread(target=Functor.print_queue)
    thread_item.start()
    thread_item.join(timeout=100)
