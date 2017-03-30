import json
import pika
from uuid import getnode as get_mac


# Names for RabbitMQ queues
class RabbitMQBase:
    # Host Server group
    QUOTE = 'quoteIn'
    AUDIT = 'AuditIn'
    WEB = 'webIn'

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
        self.param = pika.ConnectionParameters('142.104.91.142',44429)
        # self.channel = self.connection.channel(self.send)
        #
        # self.channel.queue_declare(self.send,queue=self.queueName, arguments=args)

        self.connection = pika.SelectConnection(parameters=self.param,on_open_callback=self.send)
        try:
            self.connection.ioloop.start()
        except:
            self.connection.close()
            self.connection.ioloop.start()

    def on_open(self):
        self.channel = self.connection.channel(self.send)
    # webserver should be using priority=1 when sending
    def send(self, requestBody, priority=2):

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
        self.connection.close()



    def close(self):
        self.connection.close()

# usage: RabbitMQReceiver(on_request, RabbitMQClient.QUOTE)
class RabbitMQReceiver(RabbitMQBase):
    def __init__(self, callback, queueName):
        connection = pika.BlockingConnection(pika.ConnectionParameters('142.104.91.142',44429))
        channel = connection.channel()

        args = {'x-max-priority': 3  , 'x-message-ttl': 600000}
        channel.queue_declare(queue=queueName, arguments=args)

        channel.basic_consume(callback, queue=queueName, no_ack=True , exclusive=True)

        channel.start_consuming()

