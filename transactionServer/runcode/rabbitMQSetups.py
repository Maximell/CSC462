import json
import pika
import time


class RabbitMQBase:
    QUOTE = 'quoteIn'
    DATABASE = 'databaseIn'
    TRANSACTION = 'transactionIn'
    TRIGGERS = 'triggersIn'
    AUDIT = 'AuditIn'
    WEB = 'webIn'

# this will replace having to write multiple clients
# usage: quoteClient = RabbitMQClient(RabbitMQClient.QUOTE)
# quoteClient.send({a: requestBody})
class RabbitMQClient(RabbitMQBase):
    def __init__(self, queueName):
        self.queueName = queueName
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()

        args = {'x-max-priority': 2}
        self.channel.queue_declare(queue=self.queueName, arguments=args)

    # webserver should be using priority=1 when sending
    def send(self, requestBody, priority=2):
        print "sending", requestBody, "to", self.queueName, "with priority", priority
        properties = pika.BasicProperties(
            priority=priority
        )
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queueName,
            properties=properties,
            body=json.dumps(requestBody)
        )

    def close(self):
        self.channel.close()

# usage: RabbitMQReceiver(on_request, RabbitMQClient.QUOTE)
class RabbitMQReceiver(RabbitMQBase):
    def __init__(self, callback, queueName):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()

        args = {'x-max-priority': 2}
        channel.queue_declare(queue=queueName, arguments=args)

        channel.basic_consume(callback, queue=queueName)

        channel.start_consuming()

class RabbitMQPeriodicReceiver(RabbitMQBase):
    def __init__(self, callback, periodicCallback, periodicInterval, queueName):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()

        args = {'x-max-priority': 2}
        channel.queue_declare(queue=queueName, arguments=args)

        channel.basic_consume(callback, queue=queueName)

        while True:
            print "entering forever loop"
            periodicCallback() # do the periodic task
            print "done the periodic callback"
            timeout = time.time() + periodicInterval # in seconds from now
            while time.time() < timeout:
                method, properties, body = channel.basic_get(queue=queueName)
                callback(body)
            print "out of the time loop"
