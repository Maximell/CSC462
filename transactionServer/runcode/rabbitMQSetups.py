import json
import pika


testRequest = {
    "transactionNum": 1,
    "command": 1,
    "userId": 1,
    "stockSymbol": 's',
    "quote": 200,
    "cryptoKey": 'rgeg'
}

def getQuote(request):
    if request.get('quote'):
        return "something"
    goToQuote()


def goToQuote(request):
    request['quote'] = 5
    return request


class RabbitMQBase:
    QUOTE = 'quoteIn'
    DATABASE = 'databaseIn'
    TRANSACTION = 'transactionIn'
    TRIGGERS = 'triggersIn'
    AUDIT = 'AuditIn'

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


# usage: RabbitMQReceiver(on_request, RabbitMQClient.QUOTE)
class RabbitMQReceiver(RabbitMQBase):
    def __init__(self, callback, queueName):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()

        args = {'x-max-priority': 2}
        channel.queue_declare(queue=queueName, arguments=args)

        channel.basic_consume(callback, queue=queueName)

        channel.start_consuming()