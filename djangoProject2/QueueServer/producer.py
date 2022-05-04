# -*-coding`:utf-8-*-
import json

import redisqueue

QUEUE_NAME = "queue1"
WORKER_NAME = "queue1"
QUEUE_PASS = "queue1234"
SERVER_IP = "13.209.88.71"
SERVER_PORT = 6379
DB = 0

Q_MAX_SIZE = 1000000

q = redisqueue.RedisQueuePutter(event_q_name=QUEUE_NAME , q_max_size=Q_MAX_SIZE , host=SERVER_IP , port=SERVER_PORT , db=DB)
q.put(element=json.dumps({'hits': {
    'hits': [
        "yoyo1" ,
        "yoyo2"
    ]
}}))
