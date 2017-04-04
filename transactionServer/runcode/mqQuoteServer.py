#!/usr/bin/env python
import socket
import time
import json
from random import randint
import pika
from threading import Thread
import threading
from rabbitMQSetups import RabbitMQClient, RabbitMQAyscClient, RabbitMQAyscReciever, quoteMacMap, RabbitMQBase
from mqAuditServer import auditFunctions
import Queue

import multiprocessing
from multiprocessing import Process
from uuid import getnode as get_mac


class RabbitMultiClient(RabbitMQBase):
    def __init__(self,   queueName , requestQueue ):
        self.queueNames = 	  ["transactionIn193596476298033"
                                ,"transactionIn193596744799041"
                                ,"transactionIn193597013300049"
                                ,"transactionIn193597281801057"
                                ,"transactionIn193597550302065"
                                ,"transactionIn193597818803073"
                                ,"transactionIn193598087304081"
                                ,"transactionIn193601473895188"
                                ,"transactionIn193601742334740"
                                ,"transactionIn193605068330289"
                                ,"transactionIn193809078333764"
                                ,"transactionIn193821963432263"
                                ,"transactionIn193826241687624"
                                ,"transactionIn193830553497929"
                                ,"transactionIn193860618727760"
                                ,"transactionIn8796760983851" ]  #b132

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
        # print "setup exchange"
        for queue in self.queueNames:
            self.channel.exchange_declare(self.on_exchange_declareok,
                                       queue,)

    def on_exchange_declareok(self, unused_frame):

        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.
        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame

        """
        # print "exchange all good"
        # LOGGER.info('Exchange declared')
        for queue in self.queueNames:
            self.setup_queue(queue)

    def setup_queue(self, queueName):
        args = {'x-max-priority': 3, 'x-message-ttl': 600000}
        # print "setting up queue"
        for queue in self.queueNames:
            self.channel.queue_declare(self.on_queue_declareok, queue , arguments=args)

    def on_queue_declareok(self, method_frame):
        # print "queue all good"
        for queue in self.queueNames:
            self.channel.queue_bind(self.on_bindok, queue,
                                 self.EXCHANGE, )

    def on_bindok(self, unused_frame):
        # print "bind all good"
        # Queue bound
        self.start_publishing()

    def start_publishing(self):
        # print "start Publishing"
        # self.enable_delivery_confirmations()
        self.schedule_next_message()

    def schedule_next_message(self):
        """If we are not closing our connection to RabbitMQ, schedule another
        message to be delivered in PUBLISH_INTERVAL seconds.

        """
        # print "schedule next msg"
        # if self.stopping:
        #     return
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
        noDump = True
        while(noDump):
            try:
                print "getting request"
                payload  = self.requestQueue.get()
                if payload:
                    worderId = payload[0]
                    requestBody = payload[1]
                    priority = payload[2]

                    print "sending", requestBody, "to", worderId, "with priority", priority
                    print "queue size:",   self.requestQueue.qsize()
                    self.channel.basic_publish(
                        exchange=self.EXCHANGE,
                        routing_key=worderId,
                        properties=priority,
                        body=json.dumps(requestBody),
                    )
                   # print "schedule next msg"
                # self.schedule_next_message()
            except Exception as e:
                print e
                print "had troubles sending into rabbit"
                # notEmpty = False
                # print "failed in send"

        # exit after dumplog has been sent
        # print "sentDumplog"
        # # print payload
        # # print worderId
        # # print workerMap
        # # sleep for five seconds before shutdown
        # time.sleep(5)
        # os.system("echo killall python...")
        # os.system("killall python")


    def close(self):
        self.connection.close()


class RabbitQuoteClient():
    def __init__(self,  requestQueue ):
        print "start making quoteClient"
        self.queueName = None
        self.param = pika.ConnectionParameters('142.104.91.142',44429)
        self.connection = pika.SelectConnection(self.param,self.send,stop_ioloop_on_close=False)
        self.closing = False

        self.request = None
        self.priority = None

        self.stopping = False
        self.PUBLISH_INTERVAL = 1
        self.requestQueue = requestQueue
        self.EXCHANGE = "transActionMessages"
        print "set up quoteClient finished"
        self.connection.ioloop.start()



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
        # This is the old connection IOLoop instance, stop its ioloop
        self.connection.ioloop.stop()

        # Create a new connection
        self.connection = pika.SelectConnection(self.param,self.send,stop_ioloop_on_close=False)

        # There is now a new connection, needs a new ioloop to run
        self.connection.ioloop.start()

    def on_connection_open(self , blank_connection= None):
        print "on open connection"
        self.add_on_connection_close_callback()
        self.open_channel()

    def open_channel(self):
        try:
            print "open Channel for quotes"
            self.connection.channel(on_open_callback=self.on_channel_open)
        except Exception as e:
            print "failed"
            print e

    def on_channel_open(self ):
        print "on open channel for quotes"
        # This may be wrong
        self.channel = self.connection.channel(self.sendMessage)
        self.add_on_channel_close_callback()
        self.setup_exchange(self.queueName)

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
                                       exchange_name)

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
        print "setting up queue", queueName
        self.on_connection_open()

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
        print "schedule next msg"
        if self.stopping:
            return

        self.connection.add_timeout(self.PUBLISH_INTERVAL,
                                     self.sendMessage)


    def close_connection(self):

        """This method closes the connection to RabbitMQ."""
        # LOGGER.info('Closing connection')
        print "closing connection... done"
        self.closing = True
        self.connection.close()

    def sendMessage(self ):
        print "sending", self.request, "to", self.queueName, "with priority", self.priority
        properties = pika.BasicProperties(
            content_type='application/json',
            priority=self.priority,
        )
        self.channel.basic_publish(
            exchange=self.EXCHANGE,
            routing_key=self.queueName,
            properties=properties,
            body=json.dumps(self.request),

        )
        # print "schedule next msg"
        self.send()


    def send(self , blank_connection=None):
        print "try sending"
        notEmpty = True
        while(notEmpty):
            try:
                payload  = self.requestQueue.get(False)
                if payload:
                    print "payload size =", len(payload)
                    if len(payload) == 2:
                        requestBody = payload[0]
                        self.queueName = payload[1]
                        priority = 2

                    else:
                        requestBody = payload
                        priority = 2
                    #     set up queue on the fly
                    args = {'x-max-priority': 3, 'x-message-ttl': 600000}
                    print "setting up queue",  self.queueName
                    self.request = requestBody
                    self.priority = priority
                    # self.channel.queue_declare(self.sendMessage ,self.queueName, arguments=args)
                    self.on_connection_open()



            except:
                pass
                # notEmpty = False
                # print "failed in send"



def close(self):
        self.connection.close()


def createQuoteRequest(userId, stockSymbol, lineNum, args):
    args.update({"userId": userId, "stockSymbol": stockSymbol, "lineNum": lineNum})
    return args

class poolHandler(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        # print "starting thread for poolhandler"
        #         look between pool of requests
        #          and the cache size.
        while(True):
           for sym in quoteServer.pool.keys():
                # print "things in pool:",sym
                # print "pool size:",len(quoteServer.pool)
                quote = quoteServer.quoteCache.get(sym)
                # print "cache = ", quote
                if quote is not None:
                    for payload in quoteServer.pool[sym]:
                        # payload = quoteServer.pool[sym][payloadKey]
                        # print "found a match for: ", sym
                        # if payload sym in cache
                        payload["quote"] = quote["value"]
                        payload["cryptoKey"] = quote["cryptoKey"]
                        payload["quoteRetrieved"] = quote["retrieved"]

                        transactionServerID = payload["trans"]
                        print "sending back form handler:", payload, "to",transactionServerID

                        # Need to figure out which transaction server to send back to.
                        # transactionClient = RabbitMQClient(transactionServerID)
                        # transactionClient.send(payload)
                        # transactionClient.close()
                        # requestQueue = multiprocessing.Queue()
                        # trans_producer_process = Process(target=RabbitMQAyscClient,
                        #                                  args=(transactionServerID, requestQueue))
                        # trans_producer_process.start()
                        # requestQueue.put(payload)
                        transQueue.put((payload , transactionServerID))
                        # print "popping sym" ,  quoteServer.pool
                        quoteServer.pool.pop(sym , None)
                        # print "popped", quoteServer.pool
                    print "not starting another handler"
                    # poolHandler()



class getQuoteThread(Thread):
    def __init__(self , symbol , user , transactionNum , transactionServerID):
        Thread.__init__(self)
        self.cacheLock = threading.Lock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.daemon = True
        # package to go to quote server
        self.symbol = symbol
        self.userId = user
        self.transactionNum = transactionNum
        self.transServer = transactionServerID
        # self.portNum  = portNum
        self.start()

    def run(self):
        request = self.symbol + "," + self.userId + "\n"

        self.socket.connect(('quoteserve.seng.uvic.ca', 4442 ))
        self.socket.send(request)
        data = self.socket.recv(1024)
        self.socket.close()

        newQuote = quoteServer.quoteStringToDictionary(data)
        # newQuote = {"value": 10, "cryptoKey": 'abc', "retrieved": int(time.time())}
        print "got new quote from server: ", newQuote
        requestBody = auditFunctions.createQuoteServer(
            int(time.time() * 1000),
            "quoteServer",
            self.transactionNum,
            self.userId,
            newQuote['serverTime'],
            self.symbol,
            newQuote['value'],
            newQuote['cryptoKey']
        )
        # print "built request: ",requestBody
        auditQueue.put(requestBody)
        transQueue.put((payload, self.transServer))

        # self.cacheLock.acquire()
        quoteServer.quoteCache[self.symbol] = newQuote
        # del quoteServer.inflight[quoteServer.inflight.index(self.symbol)]
        quoteServer.threadCount -= 1

        print "thread terminating"
        # self.cacheLock.release()


# quote shape: symbol: {value: string, retrieved: epoch time, user: string, cryptoKey: string}
class Quotes():
    def __init__(self, cacheExpire=60, ):
        self.cacheExpire = cacheExpire
        self.quoteCache = {}
        # self.inflight = []
        self.pool = {}
        self.threadCount = 0
        self.maxthread = 300

    def getQuote(self, symbol , user , transactionNum , transactionServerID):
        cache = self.quoteCache.get(symbol)
        print "checking quote cache: ", cache,  symbol
        # print "current cache = ",self.quoteCache
        if cache:
            if self._cacheIsActive(cache):
                print "cache value is active"
                return cache
        self.hitQuoteServerAndCache(symbol, user, transactionNum , transactionServerID)
        return

    def hitQuoteServerAndCache(self, symbol, user, transactionNum , transactionServerID):
        # run new quote thread
        # poolHandler()
        # if symbol in self.inflight:
        #     return
        # loop while there are no threads left
        while(quoteServer.maxthread <= quoteServer.threadCount):
            pass
        getQuoteThread(symbol , user , transactionNum , transactionServerID)
        print "making new thread"
        quoteServer.threadCount += 1
        print "current thread count = ",quoteServer.threadCount
        # self.inflight.append(symbol)

    def quoteStringToDictionary(self, quoteString):
        # "quote, sym, userId, timeStamp, cryptokey\n"
        split = quoteString.split(",")
        return {'value': float(split[0]), 'retrieved': int(split[3])/1000, 'serverTime': split[3], 'cryptoKey': split[4].strip("\n")}

    def _cacheIsActive(self, quote):
        print "_cacheIsActive", (int(quote.get('retrieved', 0)) + self.cacheExpire),  int(time.time())
        print "returning", (int(quote.get('retrieved', 0)) + self.cacheExpire) > int(time.time())
        return (int(quote.get('retrieved', 0)) + self.cacheExpire) > int(time.time())

    def _mockQuoteServer(self, queryString):
        query = queryString.split(",")
        symbol = query[0]
        user = query[1]
        quoteArray = [randint(0, 50), symbol, user, int(time.time()), "cryptokey" + repr(randint(0, 50))]
        return ','.join(map(str, quoteArray))

    def _printQuoteCacheState(self):
        print self.quoteCache

    def addRequestToPool(self, payload):

        symbol = payload["stockSymbol"]
        print "adding to pool", symbol
        if self.pool.get(symbol) is None:
            self.pool[symbol] = []
        self.pool[symbol].append(payload)
        print "pool is now/:", self.pool



def on_request(ch, method, props, payload):
    # expected body: {symbol, userId, transactionNum}
    print "received payload", payload

    # if payload.get("quoteRetrieved"):
    #     transQueue.put((payload, payload["trans"]))
    #     return

    symbol = payload["stockSymbol"]
    userId = payload["userId"]
    lineNum = payload["lineNum"]
    transactionServerID = payload["trans"]

    quote = quoteServer.getQuote(symbol, userId, lineNum , transactionServerID)
    # quote = {"value": 10, "cryptoKey": 'abc', "retrieved": int(time.time())}
    print "return from quote cache: ", quote
#     go in pool
    if quote is None:
        "thread gone to quote server"
        return
# ***
    # print "quote: ", quote

    payload["quote"] = quote["value"]
    payload["cryptoKey"] = quote["cryptoKey"]
    payload["quoteRetrieved"] = quote["retrieved"]

    # print "sending back from cache:", payload
    transactionServerID = payload["trans"]
    # Need to figure out which transaction or trigger server to send back to.
    print "adding payload to Queue",payload, transactionServerID
    transQueue.put((payload , transactionServerID))
    # transactionClient = RabbitMQClient(transactionServerID)
    # transactionClient.send(payload)
    # transactionClient.close()


if __name__ == '__main__':
    mac = str(get_mac())
    print "starting QuoteServer " + quoteMacMap[mac]
    quoteServer = Quotes()
    poolHandler()

    # print "create publisher"
    # transQueue = multiprocessing.Queue()
    # trans_producer_process = Process(target=RabbitQuoteClient, args=([transQueue]))
    # trans_producer_process.start()
    # print "created publisher"
    print "create publisher"
    transQueue = multiprocessing.Queue()
    producer_process = Process(target=RabbitMultiClient,
                               args=( RabbitMQBase.TRANSACTION,transQueue))
    producer_process.start()
    print "created publisher"


    # print "create publisher"
    auditQueue = multiprocessing.Queue()
    audit_producer_process = Process(target=RabbitMQAyscClient,
                               args=(  RabbitMQAyscClient.AUDIT , auditQueue ))
    audit_producer_process.start()
    print "created publisher"


    P1Q_rabbit = multiprocessing.Queue()
    P2Q_rabbit = multiprocessing.Queue()
    P3Q_rabbit = multiprocessing.Queue()

    print "Created multiprocess PriorityQueues"
    consumer_process = Process(target=RabbitMQAyscReciever,
                               args=(RabbitMQAyscReciever.QUOTE_BASE + quoteMacMap[mac], P1Q_rabbit, P2Q_rabbit, P3Q_rabbit))
    consumer_process.start()
    print "Created multiprocess Consummer"

    while (True):
        try:
            msg = P2Q_rabbit.get(False)
            if msg:
                payload = msg[1]
                props = msg[0]
                print "queue size: ", P2Q_rabbit.qsize()
                on_request(None, None, props, payload)
                continue
        except:
            pass

