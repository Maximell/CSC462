import json
import pika
from uuid import getnode as get_mac
import Queue
from threading import Thread

class consumer (Thread):
    def __init__(self , queueName):
        Thread.__init__(self)
        self.daemon = True
        self.rabbitReceiver = rabbitConsumer(self.queueName)
        self.queueName = queueName
        self.start()




class rabbitConsumer():
    def __init__(self , queueName):
        self.queue = Queue.PriorityQueue()
        self.connection = RabbitMQReceiver(self.consume , queueName)

    def consume(self, ch, method, props, body):
        payload = json.loads(body)
        print "got one"
        if props.priority == 1:
            # flipping priority b/c Priority works lowestest to highest
            # But our system works the other way.

            # We need to display lineNum infront of payload to so get() works properly
            self.queue.put((2, [payload["lineNum"] , payload]))
        else:
            self.queue.put((1, [payload["lineNum"] , payload]))


# Names for RabbitMQ queues
class RabbitMQBase:
    # Host Server group
    QUOTE = 'quoteIn'
    AUDIT = 'AuditIn'

    mac = str(get_mac())
    #Worker group
    DATABASE = 'database' + mac
    TRANSACTION = 'transactionIn' + mac
    TRIGGERS = 'triggersIn' + mac


# this will replace having to write multiple clients
# usage: quoteClient = RabbitMQClient(RabbitMQClient.QUOTE)
# quoteClient.send({a: requestBody})
class RabbitMQClient(RabbitMQBase):
    def __init__(self, queueName):
        self.queueName = queueName
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('142.104.91.142',44429))
        self.channel = self.connection.channel()

        args = {'x-max-priority': 2}
        self.channel.queue_declare(queue=self.queueName, arguments=args)

    # webserver should be using priority=1 when sending
    def send(self, requestBody, priority=2):
        try:
            print "sending", requestBody, "to", self.queueName, "with priority", priority
            properties = pika.BasicProperties(
                priority=priority,
            )
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queueName,
                properties=properties,
                body=json.dumps(requestBody),

            )
        except:
            print "Problem with request body"
            print requestBody


# usage: RabbitMQReceiver(on_request, RabbitMQClient.QUOTE)
class RabbitMQReceiver(RabbitMQBase):
    def __init__(self, callback, queueName):
        connection = pika.BlockingConnection(pika.ConnectionParameters('142.104.91.142',44429))
        channel = connection.channel()

        args = {'x-max-priority': 2}
        channel.queue_declare(queue=queueName, arguments=args)

        channel.basic_consume(callback, queue=queueName, no_ack=True)

        channel.start_consuming()
