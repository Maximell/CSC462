import json
import pika

# this will replace having to write multiple clients
# usage: quoteClient = RabbitMQClient(RabbitMQClient.QUOTE)
# quoteClient.send({a: requestBody})
class RabbitMQClient:
    QUOTE = 'quoteIn'
    DATABASE = 'databaseIn'
    WEBSERVER = 'webserverIn'
    TRIGGERS = 'triggersIn'
    AUDIT = 'AuditIn'

    def __init__(self, queueName):
        self.queueName = queueName
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queueName)

    def send(self, requestBody):
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queueName,
            body=json.dumps(requestBody)
        )