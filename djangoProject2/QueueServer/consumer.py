# -*-coding:utf-8-*-

import os
import sys

# import tasks

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

# 상대경로의 횟수만큼 .을찍는다


QUEUE_NAME = "qbgkek-redisqueue-server"
# SERVER_IP = "localhost"
SERVER_IP = "localhost"

SERVER_PORT = 6379
DB = 0

isEmpty_Queue = True

'''
q = RedisQueue(QUEUE_NAME, host=SERVER_IP, port=SERVER_PORT, db=DB)

while isEmpty_Queue:
    msg = q.get(isBlocking=True)

    if msg == None:
        print(time.time(), "queue 대기...")

    if msg is not None:
        msg = json.loads(msg.decode("utf-8"))
        print(msg)
'''
