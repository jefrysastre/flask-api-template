import stomp


class StompNotification:
    def __init__(self, user, password, server='localhost', port=61613, use_ssl=True):
        self.server = server
        self.port = port
        self.use_ssl = use_ssl

        self.user= user
        self.password = password

        self.queue_ids = 0
        self.queues = {}

    def send(self, data, queue='queue/notification'):

        _connection = stomp.Connection(
            host_and_ports=[(self.server, self.port)],
            use_ssl=False
        )
        try:
            _connection.connect(self.user, self.password , wait=True)
        except stomp.exception.ConnectFailedException as e:
            return False

        if queue not in self.queues:
            self.queue_ids = self.queue_ids + 1
            self.queues[queue] = self.queue_ids

        _queue_id = self.queues[queue]
        _connection.subscribe(queue, _queue_id)

        _connection.send(
            body=data,
            destination=queue
        )

        # _connection.unsubscribe(id=_queue_id)
        _connection.disconnect()

        return True
