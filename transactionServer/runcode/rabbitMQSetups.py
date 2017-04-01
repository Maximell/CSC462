import json
import pika
from uuid import getnode as get_mac

quoteMacMap = {
    '193595670795008': "1",
    '193599966811136': "2",
    '193600282694676': "3"
}

# Names for RabbitMQ queues
class RabbitMQBase:
    # Host Server group
    # TODO: remove 'quote' once triggers is moved over as well
    QUOTE_BASE = 'quoteIn'

    QUOTE1 = 'quoteIn1'
    QUOTE2 = 'quoteIn2'
    QUOTE3 = 'quoteIn3'

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

    def send(self, requestBody , priority=2):
        # print "sending", requestBody, "to", self.queueName, "with priority", priority
        proporties = pika.BasicProperties(
            priority=priority
        )
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queueName,
            properties=proporties,
            body=json.dumps(requestBody),

        )

# This is for the aysnc rabbitMQ Publisher
class RabbitMQAyscClient(RabbitMQBase):
    def __init__(self, queueName , requestQueue ):
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

        self.connection.ioloop.start()

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
        args = {'x-max-priority': 3, 'x-message-ttl': 600000}
        print "setting up queue"
        self.channel.queue_declare(self.on_queue_declareok, queueName , arguments=args)

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
        notEmpty = True
        while(notEmpty):
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
                pass
                # notEmpty = False
                # print "failed in send"


    def close(self):
        self.connection.close()

# ^ all for aysc connection and reliability
# ==================================================================


# This is for the aysnc rabbitMQ Consumer
class RabbitMQAyscReciever(RabbitMQBase):
    def __init__(self, queueName , rabbitPQueue1 , rabbitPQueue2=None , rabbitPQueue3=None ):
        self.queueName = queueName
        self.param = pika.ConnectionParameters('142.104.91.142',44429)
        self.connection = pika.SelectConnection(self.param, self.on_connection_open, stop_ioloop_on_close=False)
        self.channel = None
        self.closing = False
        self.stopping = False
        self.PUBLISH_INTERVAL = 1

        self.rabbitPQueue1 = rabbitPQueue1
        self.rabbitPQueue2 = rabbitPQueue2
        self.rabbitPQueue3 = rabbitPQueue3

        self.EXCHANGE = queueName
        self.deliveries = []
        self.acked = 0
        self.nacked = 0
        self.message_number = 0
        self.consumer_tag = None
        print "set up Consumer"

        self.connection.ioloop.start()

    def connect(self):
        return pika.SelectConnection(self.param, self.on_connection_open, stop_ioloop_on_close=False)

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
        self.deliveries = []
        self.acked = 0
        self.nacked = 0
        self.message_number = 0
        self.connection.ioloop.stop()

        if not self.closing:
            # This is the old connection IOLoop instance, stop its ioloop

            # Create a new connection
            self.connection = self.connect()

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
        self.connection.close()

    def setup_exchange(self, exchange_name):
        print "setup exchange"
        self.channel.exchange_declare(self.on_exchange_declareok,
                                       self.queueName)

    def on_exchange_declareok(self, unused_frame):

        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.
        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame

        """
        print "exchange all good"
        # LOGGER.info('Exchange declared')
        self.setup_queue(self.queueName)

    def setup_queue(self, queueName):
        args = {'x-max-priority': 3, 'x-message-ttl': 600000}
        print "setting up queue"
        self.channel.queue_declare(self.on_queue_declareok, queueName , arguments=args)

    def on_queue_declareok(self, method_frame):
        print "queue all good"
        self.channel.queue_bind(self.on_bindok, self.queueName,
                                 self.EXCHANGE, )

    def on_bindok(self, unused_frame):
        print "bind all good"
        # Queue bound
        self.start_consuming()

    def start_consuming(self):
        print "start Consuming"
        # self.enable_delivery_confirmations()
        self.add_on_cancel_callback()
        self.consumer_tag = self.channel.basic_consume(self.on_message,
                                                         self.queueName , no_ack=True)
    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.

        """
        self.channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame
        """

        if self.channel:
            self.channel.close()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.

        :param pika.channel.Channel unused_channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param str|unicode body: The message body

        # """
        # LOGGER.info('Received message # %s from %s: %s',
        #             basic_deliver.delivery_tag, properties.app_id, body)
        # self.acknowledge_message(basic_deliver.delivery_tag)
        payload = json.loads(body)
        print "Received :", payload
        print "priority = ", properties.priority

        if properties.priority == 1:
            self.rabbitPQueue1.put((1,  payload))
        elif properties.priority == 2:
            self.rabbitPQueue2.put((2, payload))
        else:
            self.rabbitPQueue3.put((3,  payload))

    def close_connection(self):

        """This method closes the connection to RabbitMQ."""
        # LOGGER.info('Closing connection')
        print "closing connection... done"
        self.closing = True
        self.connection.close()


    def close(self):
        self.connection.close()

# ^ all for aysc connection and reliability of a consumer
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

