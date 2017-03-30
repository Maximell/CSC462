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
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('142.104.91.142', 44429))
        self.channel = self.connection.channel()

        args = {'x-max-priority': 3 , 'x-message-ttl': 600000 }
        self.channel.queue_declare(queue=self.queueName, arguments=args)

    def send(self, requestBody ):
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queueName,
            properties=2,
            body=json.dumps(requestBody),

        )

# This is for the aysnc rabbitMQ
class RabbitMQAyscClient(RabbitMQBase):
    def __init__(self, queueName , requestQueue  ):
        self.queueName = queueName
        self.param = pika.ConnectionParameters('142.104.91.142',44429)
        self.connection = pika.SelectConnection(self.param,self.on_connection_open,stop_ioloop_on_close=False)
        self.channel = None
        self.closing = False
        self.stopping = False
        self.PUBLISH_INTERVAL = 1
        self.requestQueue = requestQueue
        self.EXCHANGE = queueName
        print "set up Publisher"


    def on_connection_open(self , blank_connection):
        print "on open connection"
        self.add_on_connection_close_callback()
        self.open_channel()

    def add_on_connection_close_callback(self):
        print "on closed connection do callback"
        self.connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):


        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        :param pika.connection.Connection connection: The closed connection obj
        :param int reply_code: The server provided reply_code if given
        :param str reply_text: The server provided reply_text if given

        """
        print "on Closed connection"
        self._channel = None
        if self.closing:
            self.connection.ioloop.stop()
        else:
            # LOGGER.warning('Connection closed, reopening in 5 seconds: (%s) %s',
            #                reply_code, reply_text)
            self.connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        """Will be invoked by the IOLoop timer if the connection is
        closed. See the on_connection_closed method.

        """
        print "reconnecting"
        self._deliveries = []
        self._acked = 0
        self._nacked = 0
        self._message_number = 0

        # This is the old connection IOLoop instance, stop its ioloop
        self.connection.ioloop.stop()

        # Create a new connection
        self.connection = pika.SelectConnection(self.param,self.on_connection_open,stop_ioloop_on_close=False)

        # There is now a new connection, needs a new ioloop to run
        self.connection.ioloop.start()

    def open_channel(self):
        print "open Channel"
        self.connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self , channel):
        print "on open channel"
        self.channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange(self.EXCHANGE)

    def add_on_channel_close_callback(self):

        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.
        """
        print "callback after channel closed"
        self.channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        """Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.

        :param pika.channel.Channel: The closed channel
        :param int reply_code: The numeric reason the channel was closed
        :param str reply_text: The text reason the channel was closed

        """
        print "channel closed"
        # LOGGER.warning('Channel was closed: (%s) %s', reply_code, reply_text)
        if not self.closing:
            self.connection.close()

    def setup_exchange(self, exchange_name):
        print "setup exchange"
        self.channel.exchange_declare(self.on_exchange_declareok,
                                       self.queueName,)

    def on_exchange_declareok(self, unused_frame):

        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.
        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame

        """
        print "exchange all good"
        # LOGGER.info('Exchange declared')
        self.setup_queue(self.queueName)

    def setup_queue(self, queueName):
        print "setting up queue"
        self.channel.queue_declare(self.on_queue_declareok, queueName)

    def on_queue_declareok(self, method_frame):
        print "queue all good"
        self.channel.queue_bind(self.on_bindok, self.queueName,
                                 self.EXCHANGE, )

    def on_bindok(self, unused_frame):
        print "bind all good"
        # Queue bound
        self.start_publishing()

    def start_publishing(self):
        print "start Publishing"
        # self.enable_delivery_confirmations()
        self.schedule_next_message()

    def schedule_next_message(self):
        """If we are not closing our connection to RabbitMQ, schedule another
        message to be delivered in PUBLISH_INTERVAL seconds.

        """
        print "scheduale next msg"
        if self.stopping:
            return
        # LOGGER.info('Scheduling next message for %0.1f seconds',
        #             self.PUBLISH_INTERVAL)
        self.connection.add_timeout(self.PUBLISH_INTERVAL,
                                     self.send)


    def close_connection(self):

        """This method closes the connection to RabbitMQ."""
        # LOGGER.info('Closing connection')
        print "closing connection... done"
        self.closing = True
        self.connection.close()


    def send(self):
        print "try sending"
        try:
            payload  = self.requestQueue.get(False)
            if payload:
                if len(payload) == 2:
                    requestBody = payload[0]
                    self.queueName = payload[1]
                else:
                    requestBody = payload
                priority = 2

                print "sending", requestBody, "to", self.queueName, "with priority", priority
                properties = pika.BasicProperties(
                    content_type='application/json',
                    priority=priority,
                )
                self.channel.basic_publish(
                    exchange=self.EXCHANGE,
                    routing_key=self.queueName,
                    properties=properties,
                    body=json.dumps(requestBody),

                )
                print "schedule next msg"
                self.schedule_next_message()
        except:
            print "failed in send"


    def close(self):
        self.connection.close()

# ^ all for aysc connection and reliability
# ==================================================================

# usage: RabbitMQReceiver(on_request, RabbitMQClient.QUOTE)
class RabbitMQReceiver(RabbitMQBase):
    def __init__(self, callback, queueName):
        connection = pika.BlockingConnection(pika.ConnectionParameters('142.104.91.142',44429))
        channel = connection.channel()

        args = {'x-max-priority': 3  , 'x-message-ttl': 600000}
        channel.queue_declare(queue=queueName, arguments=args)

        channel.basic_consume(callback, queue=queueName, no_ack=True , exclusive=True)

        channel.start_consuming()

