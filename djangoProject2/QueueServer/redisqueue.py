import redis


class RedisQueue:
    def __init__(self , name , **redis_kwargs):
        self.key = name
        self.rq = redis.Redis(**redis_kwargs)

    # Get Queue Size
    def size(self):
        return self.rq.llen(self.key)

    # isEmpty
    def isEmpty(self):
        return self.size() == 0

    # input Data
    def put(self , element):
        try:
            self.rq.lpush(self.key , element)
            return True

        except Exception as e:
            return False

    # output data
    def get(self , isBlocking=False , timeout=None):
        if isBlocking:
            element = self.rq.brpop(self.key)  # blocking right pop
            element = element[1]
        else:
            element = self.rq.rpop(self.key)  # right pop

        return element

    def get_without_pop(self):  # select pop data
        if self.isEmpty():
            return None
        element = self.rq.lindex(self.key , -1)
        return element


class RedisQueuePutter:
    def __init__(self , event_q_name , q_max_size=100000 , **redis_kwargs):
        self.event_q_name = event_q_name
        self.q_max_size = q_max_size
        self.rqueue = redis.Redis(**redis_kwargs)

    def put(self , element):
        self.rqueue.lpush(self.event_q_name , element)  # left push

        # q_max_size를 초과한 경우 잘라서 작업
        self.rqueue.ltrim(self.event_q_name , 0 , self.q_max_size - 1)


class RedisQueueWorker:
    def __init__(self , event_q_name , worker_q_name , q_max_size=100000 , **redis_kwargs):
        self.event_q_name = event_q_name
        self.worker_q_name = worker_q_name
        self.q_max_size = q_max_size
        self.rqueue = redis.Redis(**redis_kwargs)

    def get_rqueue(self):
        return self.rqueue

    def get_msg(self , isBlocking=False , timeout=None):  # popping data
        # if workerQueue contains queue data?
        if (self.rqueue.llen(self.worker_q_name) >= 1):
            return self.rqueue.lindex(self.worker_q_name , -1)

        # event queue에 메세지가 있다면 워커큐로 옮기고 메세지를 리턴
        if isBlocking:
            return self.rqueue.brpoplpush(self.event_q_name , self.worker_q_name)

        else:
            return self.rqueue.rpoplpush(self.event_q_name , self.worker_q_name)

    def done_msg(self , value):
        return self.rqueue.lrem(self.worker_q_name , 0 , value)
