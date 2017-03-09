import json
import pika

# Names for RabbitMQ queues
class RabbitMQBase:
    # Host Server group
    QUOTE = 'quoteIn'
    AUDIT = 'AuditIn'

    #Worker group
    DATABASE = 'database'
    TRANSACTION = 'transactionIn'
    TRIGGERS = 'triggersIn'


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


# usage: RabbitMQReceiver(on_request, RabbitMQClient.QUOTE)
class RabbitMQReceiver(RabbitMQBase):
    def __init__(self, callback, queueName):
        connection = pika.BlockingConnection(pika.ConnectionParameters('142.104.91.142',44429))
        channel = connection.channel()

        args = {'x-max-priority': 2}
        channel.queue_declare(queue=queueName, arguments=args)

        channel.basic_consume(callback, queue=queueName)

        channel.start_consuming()
