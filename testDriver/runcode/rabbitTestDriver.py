import sys
import time
from pprint import pprint
import json
import pika
import multiprocessing
from multiprocessing import Process
from multiprocessing import Queue
import gc
class RabbitMQBase:
    TRANSACTION = 'transactionIn193596476298033'

# tried to import -> code completion worked, running it didnt, why is python like this
# from transactionServer.runCode.rabbitMQSetups import RabbitMQClient
# class RabbitMQClient():
    # def __init__(self, queueName):
    #     self.queueName = queueName
    #     self.connection = pika.BlockingConnection(pika.ConnectionParameters('142.104.91.142', 44429))
    #     self.channel = self.connection.channel()
    #
    #     args = {'x-max-priority': 3 , 'x-message-ttl': 600000}
    #     self.channel.queue_declare(queue=self.queueName, arguments=args)
    #
    # def send(self, requestBody , properties):
    #     self.channel.basic_publish(
    #         exchange='',
    #         routing_key=self.queueName,
    #         properties=properties,
    #         body=json.dumps(requestBody),
    #
    #     )

# This is for the aysnc rabbitMQ
class RabbitMQAyscClient(RabbitMQBase):
    def __init__(self,  requestQueue , queueName ):
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
        # print "on open connection"
        self.add_on_connection_close_callback()
        self.open_channel()

    def add_on_connection_close_callback(self):
        # print "on closed connection do callback"
        self.connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):


        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        :param pika.connection.Connection connection: The closed connection obj
        :param int reply_code: The server provided reply_code if given
        :param str reply_text: The server provided reply_text if given

        """
        # print "on Closed connection"
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
        # print "reconnecting"
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
        # print "open Channel"
        self.connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self , channel):
        # print "on open channel"
        self.channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange(self.EXCHANGE)

    def add_on_channel_close_callback(self):

        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.
        """
        # print "callback after channel closed"
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
        # print "channel closed"
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
        # for queue in self.queueNames:
        self.channel.queue_declare(self.on_queue_declareok, queueName , arguments=args)

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
        # print "scheduale next msg"
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
        # print "try sending"
        noDump = True
        while(noDump):
            try:
                payload  = self.requestQueue.get()
                if payload:
                    worderId = payload[0]
                    requestBody = payload[1]
                    priority = payload[2]

                    # print "sending", requestBody, "to", worderId, "with priority", priority
                    print self.requestQueue.qsize()
                    self.channel.basic_publish(
                        exchange=self.EXCHANGE,
                        routing_key=worderId,
                        properties=priority,
                        body=json.dumps(requestBody),

                    )
                    if requestBody["command"] == "DUMPLOG":
                        noDump = False
                        break
                    self.schedule_next_message()
                # print "schedule next msg"

            except Exception as e:
                print e
                print "exception in sending"
                self.schedule_next_message()
                pass
                # notEmpty = False
                # print "failed in send"

        # exit after dumplog has been sent
        print "sentDumplog"
        print payload
        print worderId
        print workerMap
        # sleep for five seconds before shutdown
        time.sleep(5)
        print "finished"

        # quit()


    def close(self):
        self.connection.close()
# Worker machines via queues + mac
# workerMap = [
#     #  QueueName , [NumOfUsers , Number of Commands]
#     [RabbitMQClient("transactionIn193596476298033"), [0 , 0]], #B01331331331
#     [RabbitMQClient("transactionIn193596744799041"), [0 , 0]], #B01341341341
#     [RabbitMQClient("transactionIn193601473895188"), [0 , 0]], #B0145B145B14
#     [RabbitMQClient("transactionIn193601742334740"), [0 , 0]], #B0146B146B14
#     [RabbitMQClient("transactionIn193809078333764"), [0 , 0]], #B044B144B144
#     [RabbitMQClient("transactionIn193821963432263"), [0 , 0]], #B047B147B147
#     [RabbitMQClient("transactionIn193826241687624"), [0 , 0]], # B048B048B048
#     [RabbitMQClient("transactionIn193830553497929"), [0 , 0]], #B049B149B149
#     [RabbitMQClient("transactionIn193860618727760"), [0 , 0]], #B050B150B150
#     [RabbitMQClient("transactionIn8796760983851"), [0 , 0]] #B132
# ]
workerMap = [
    ["transactionIn193596476298033", [0, 0]],
    ["transactionIn193596744799041", [0, 0]],
    ["transactionIn193597013300049", [0, 0]],
    ["transactionIn193597281801057", [0, 0]],
    ["transactionIn193597550302065", [0, 0]],
    ["transactionIn193597818803073", [0, 0]],
    ["transactionIn193598087304081", [0, 0]],
    ["transactionIn193601473895188", [0, 0]],
    ["transactionIn193601742334740", [0, 0]],
    ["transactionIn193605068330289", [0, 0]],
    ["transactionIn193809078333764", [0, 0]],
    ["transactionIn193821963432263", [0, 0]],
    ["transactionIn193826241687624", [0, 0]],
    ["transactionIn193830553497929", [0, 0]],
    ["transactionIn193860618727760", [0, 0]],
    ["transactionIn8796760983851", [0, 0]]
]
# last mac addr queue is 132 - Haven't changed the mac yet.

# transactionClient.send(data, priority=1)

# User to Worker Mapping.
userMap = {}


def send(command, args, lineNum):
    DUMPFLAG = False
    # print "--------------------"
    # print "command", command
    # print "args", args
    # print "line", lineNum
    user = args[0]
    properties = pika.BasicProperties(priority=1)

    # get or put into userMap
    if user in userMap:
        client = userMap[user]
        for x in workerMap:
            # update the ammount in the current Worker
            if x[0] == client:
                x[1][1] += 1
                break

        # print("In dict already")
    else:
        # just need a number in the workerMap
        minUser = workerMap[0][1][0]
        index = 0
        sendto = None
        # find the worker with the fewest users
        for x in range(0, len(workerMap)):
            currentWorker = workerMap[x]
            currentAmount = currentWorker[1][1]

            if currentWorker[1][0] <= minUser:
                sendto = currentWorker
                index = x
                # print "found fewest users"
                minUser = currentWorker[1][0]
                minAmount = currentAmount
        # find the worker with fewest users and commands.
        for x in range(0 , len(workerMap)):
            currentWorker = workerMap[x]
            # if user amount is greater than minUser skip
            if currentWorker[1][0] > minUser:
                continue
            else:
                # SAme amount of user so check amount
                if currentWorker[1][1] < minAmount:
                    index = x
                    minAmount = currentWorker[1][1]
                    # print "found fewest Commands"
                    sendto = currentWorker
        if sendto != None:
            # print("adding User to map")
            userMap[user] = sendto[0]
            client = sendto[0]
            workerMap[index][1][1] += 1
            workerMap[index][1][0] += 1
        else:
            print("problem setting user map")

    # setup args to push into rabbit
    if len(args) > 2:
        args = {
            'userId': args[0],
            'stockSymbol': args[1],
            'cash': args[2]
        }
    elif len(args) == 2 and command in ['ADD']:
        args = {
            'userId': args[0],
            'cash': args[1]
        }
    elif len(args) == 2:
        args = {
            'userId': args[0],
            'stockSymbol': args[1]
        }
    elif len(args) == 1 and command in ['DUMPLOG']:
        args = {
            'userId': "./testLOG"
        }
        properties = pika.BasicProperties(priority=3)
        DUMPFLAG = True
        # return  # dont bother sending a dumplog
    elif len(args) == 1:
        args = {
            'userId': args[0]
        }

    args["command"] = command
    args["lineNum"] = lineNum

    if args.get("cash"):
        try:
            float(args["cash"])
        except:
            args["cash"] = -1

    # print "sending:", args
    # push into rabbitK
    requestQueue.put((client ,args , properties ))
    if DUMPFLAG:
        # time.sleep()
        print requestQueue.qsize()
        print workerMap


def main():
    # read file and push into queues as you are reading
    users = {}
    with open(sys.argv[1]) as f:
        for line in f:
            line = line.strip()
            splitLine = line.split(" ")

            lineNumber = splitLine[0].strip("[]")

            commandAndArgs = splitLine[1].split(",")
            command = commandAndArgs[0]
            args = commandAndArgs[1:]
            # record how many commands each user gets

            #If Dumplog then send the dumplog to the user with the highest amount of commands
            if command in ['DUMPLOG']:
                max = 0
                workerQueue = workerMap[0][0]
                for worker in workerMap:
                    if worker[1][1] > max:
                        max = worker[1][1]
                        workerQueue = worker[0]
                for user in userMap:
                    if workerQueue == userMap[user]:
                        args[0] = user
            print lineNumber
            send(command, args, lineNumber)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('INCORRECT PARAMETERS\n')
        print('python rabbitTestDriver.py  <file>')
        print('example: python rabbitTestDriver.py 2userWorkLoad.txt')
        print(sys.argv)
    else:
        DUMPFLAG = False
        requestQueue = multiprocessing.Queue()

        main()
        pprint(workerMap)
        pprint(userMap.items())
        print('completed')
        workerMap = None
        userMap = None
        gc.collect()
        # time.sleep(10)
        print "create publisher"
        RabbitMQAyscClient(requestQueue, RabbitMQBase.TRANSACTION)

        print "created publisher"
        while True:
            print requestQueue.qsize()
            time.sleep(1)

