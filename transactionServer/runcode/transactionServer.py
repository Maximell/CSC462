# demonstrate talking to the quote server
import ast
import json
import math
import socket
import time
import uuid
from random import randint

import pika

import queueNames
from AuditServer.mqAuditServer import auditFunctions
from QuoteCacheServer import createQuoteRequest
from mqDatabaseServer import databaseFunctions
from mqTriggers import TriggerFunctions


# took out old class structures

# new RPC audit client using rabbitMQ
class AuditRpcClient(object):
    def __init__(self):
        self.response = None
        self.corr_id = None

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)
    def on_response(self, ch, method, props, body):
        # make sure its the right package
        if self.corr_id == props.correlation_id:
            # self.response is essential the return of this function, because call() waits on it to be not None
            self.response = json.loads(body)

    def call(self, requestBody):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        print "sending Audit request Id:", self.corr_id
        self.channel.basic_publish(
            exchange='',
            routing_key=queueNames.AUDIT,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body=json.dumps(requestBody)
        )
        while self.response is None:
            self.connection.process_data_events()
        print "From Audit server: ", self.response
        return self.response

# new RPC client client using rabbitMQ
class QuoteRpcClient(object):
    def __init__(self):
        self.response = None
        self.corr_id = None

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        # make sure its the right package
        if self.corr_id == props.correlation_id:
            # self.response is essential the return of this function, because call() waits on it to be not None
            self.response = json.loads(body)

    def call(self, requestBody):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        print "sending quote request Id:", self.corr_id
        self.channel.basic_publish(
            exchange='',
            routing_key=queueNames.QUOTE,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body=json.dumps(requestBody)
        )
        while self.response is None:
            self.connection.process_data_events()
        print "From Quote server: ",  self.response
        return self.response

# new RPC Database client using rabbitMQ
class DatabaseRpcClient(object):
    def __init__(self):
        self.response = None
        self.corr_id = None

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        # make sure its the right package
        if self.corr_id == props.correlation_id:
            # self.response is essential the return of this function, because call() waits on it to be not None
            self.response = json.loads(body)

    def call(self, requestBody):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        print "sending Database request Id:", self.corr_id
        self.channel.basic_publish(
            exchange='',
            routing_key=queueNames.DATABASE,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body=json.dumps(requestBody)
        )
        while self.response is None:
            self.connection.process_data_events()
        print "From Database server: ",  self.response
        return self.response


class TriggerRpcClient(object):
    def __init__(self):
        self.response = None
        self.corr_id = None

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        # make sure its the right package
        if self.corr_id == props.correlation_id:
            # self.response is essential the return of this function, because call() waits on it to be not None
            self.response = json.loads(body)

    def call(self, requestBody):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        print "sending Trigger request Id:", self.corr_id , requestBody
        self.channel.basic_publish(
            exchange='',
            routing_key=queueNames.TRIGGERS,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body=json.dumps(requestBody)
        )
        while self.response is None:
            self.connection.process_data_events()
        print "From Trigger server: ",  self.response
        return self.response


# quote shape: symbol: {value: string, retrieved: epoch time, user: string, cryptoKey: string}
class Quotes():
    def __init__(self, cacheExpire=60, testing=False):
        self.cacheExpire = cacheExpire
        self.quoteCache = {}
        self.testing = testing
        # self.auditServer = auditServer
        # if not testing:
        #     self.quoteServerConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     self.quoteServerConnection.connect(('quoteserve.seng.uvic.ca', 4445))

    def getQuote(self, symbol, user, transactionNum):
        self._testPrint(True, "current cache state: ", self.quoteCache)

        cache = self.quoteCache.get(symbol)
        if cache:
            # print "in cache"
            if self._cacheIsActive(cache):
                # print "is active and using cache"
                self._testPrint(False, "from cache")
                return cache
            self._testPrint(False, "expired cache")
            # print "not active"
        # print "not from cache"
        return self._hitQuoteServerAndCache(symbol, user, transactionNum)

    '''
        this can be used on buy commands
        that way we can guarantee the 60 seconds for a commit
        if we use cache, the quote could be 119 seconds old when they commit, and that breaks the requirements
    '''

    def getQuoteNoCache(self, symbol, user, transactionNum):
        return self._hitQuoteServerAndCache(symbol, user, transactionNum)

    def _hitQuoteServerAndCache(self, symbol, user, transactionNum):
        self._testPrint(False, "not from cache")
        request = symbol + "," + user + "\n"

        if self.testing:
            data = self._mockQuoteServer(request)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('quoteserve.seng.uvic.ca', 4445))
            s.send(request)
            data = s.recv(1024)
            # print data
            # print "Hitting quoteServer"
            s.close()
            # self.quoteServerConnection.send(request)
            # data = self.quoteServerConnection.recv(1024)

        newQuote = self._quoteStringToDictionary(data)
        # LogQuoteServer

        # audit_rpc.call()
        # self.auditServer.logQuoteServer(
        #     int(time.time() * 1000),
        #     "quote",
        #     transactionNum,
        #     user,
        #     newQuote.get('serverTime'),
        #     symbol,
        #     newQuote.get('value'),
        #     newQuote.get('cryptoKey')
        # )

        self.quoteCache[symbol] = newQuote
        return newQuote

    def _quoteStringToDictionary(self, quoteString):
        # "quote, sym, userId, timeStamp, cryptokey\n"
        split = quoteString.split(",")
        return {'value': float(split[0]), 'retrieved': int(time.time()), 'serverTime': split[3], 'cryptoKey': split[4].strip("\n")}

    def _cacheIsActive(self, quote):
        return (int(quote.get('retrieved', 0)) + self.cacheExpire) > int(time.time())

    def _mockQuoteServer(self, queryString):
        query = queryString.split(",")
        symbol = query[0]
        user = query[1]
        quoteArray = [randint(0, 50), symbol, user, "cryptokey" + repr(randint(0, 50))]
        return ','.join(map(str, quoteArray))

    def _testPrint(self, newLine, *args):
        if self.testing:
            for arg in args:
                pass
                # print arg,
            if newLine:
                pass
                # print

    def _printQuoteCacheState(self):
        print self.quoteCache
        pass


def delegate(ch , method, properties, body):
    args = ast.literal_eval(body)
    try:
        # this is where we will figure what command we are dealing with
        # and deligate from here to whatever function is needed
        # to handle the request
        # ----------------------------
        # add
        # quote
        # buy
        # commit_buy
        # cancel_buy
        # sell
        # commit_sell
        # cancel_sell
        #
        # set_buy_amount
        # cancel_set_buy
        # set_buy_trigger
        #
        # set_sell_amount
        # cancel_set_sell
        # set_sell_trigger
        # ----------------------------
        # args = ast.literal_eval(body)
        print args
        # Call Quote
        # self, timeStamp, server, transactionNum, userId, commandName, stockSymbol=None, fileName=None, amount=None

        if "./testLOG" != args["userId"]:

            requestBody = auditFunctions.createUserCommand(int(time.time() * 1000),"transactionServer", args["lineNum"],
                                                args["userId"], args["command"],args.get("stockSymbol"),None,args.get("cash"))
            # Log User Command Call
            audit_rpc.call(requestBody)

        else:
            requestBody = auditFunctions.createUserCommand(int(time.time() * 1000), "transactionServer", args["lineNum"],
                                                               args["userId"], args["command"], args.get("stockSymbol"),
                                                               args["userId"], args.get("cash"))
            # Log User Command Call
            audit_rpc.call(requestBody)

        if args["command"] == "QUOTE":
            handleCommandQuote(args)

        elif args["command"] == "ADD":
            handleCommandAdd(args)

        elif args["command"] == "BUY":
            handleCommandBuy(args)

        elif args["command"] == "COMMIT_BUY":
            handleCommandCommitBuy(args)

        elif args["command"] == "CANCEL_BUY":
            handleCommandCancelBuy(args)

        elif args["command"] == "SELL":
            handleCommandSell(args)

        elif args["command"] == "COMMIT_SELL":
            handleCommandCommitSell(args)

        elif args["command"] == "CANCEL_SELL":
            handleCommandCancelSell(args)

        elif args["command"] == "SET_BUY_AMOUNT":
            handleCommandSetBuyAmount(args)

        elif args["command"] == "CANCEL_BUY_AMOUNT":
            handleCommandCancelSetBuy(args)

        elif args["command"] == "SET_BUY_TRIGGER":
            handleCommandSetBuyTrigger(args)

        elif args["command"] == "SET_SELL_AMOUNT":
            handleCommandSetSellAmount(args)

        elif args["command"] == "CANCEL_SELL_AMOUNT":
            handleCommandCancelSetSell(args)

        elif args["command"] == "SET_SELL_TRIGGER":
            handleCommandSetSellTrigger(args)
        elif args["command"] == "DUMPLOG":
            handleCommandDumplog(args)
        else:
            print "couldn't figure out command..."
            print "command: ", args
    except RuntimeError:
        # (self, timeStamp, server, transactionNum, userId, commandName, errorMessage)
        # errror msg being sent to audit server
        # requestBody = {"function": "ERROR_MESSAGE", "timeStamp": int(time.time() * 1000),
        #                "server": "transactionServer", "transactionNum": args.get('lineNum'),
        #                "userId": args.get('userId'),"command": args.get("command"), "errorMessage": RuntimeError
        #                }
        requestBody = auditFunctions.createErrorMessage(int(time.time() * 1000), "transactionServer", args["lineNum"],
                                                               args["userId"], args["command"],str(RuntimeError))
        audit_rpc.call(requestBody)
    except TypeError:
        # errror msg being sent to audit server
        requestBody = auditFunctions.createErrorMessage(int(time.time() * 1000), "transactionServer", args["lineNum"],
                                                            args["userId"], args["command"], str(TypeError))
        audit_rpc.call(requestBody)
    except ArithmeticError:
        # errror msg being sent to audit server
        requestBody = auditFunctions.createErrorMessage(int(time.time() * 1000), "transactionServer", args["lineNum"],
                                                            args["userId"], args["command"], str(ArithmeticError))
        audit_rpc.call(requestBody)

def handleCommandQuote(args):
    symbol = args["stockSymbol"]
    userId = args["userId"]
    transactionNum = args["lineNum"]

    request = createQuoteRequest(userId, symbol, transactionNum)
    response = quote_rpc.call(request)


def handleCommandAdd(args):
    request = databaseFunctions.createAddRequest(args["userId"], args["cash"])
    response = db_rpc.call(request)


def handleCommandBuy(args):
    symbol = args["stockSymbol"]
    cash = args["cash"]
    userId = args["userId"]

    request = databaseFunctions.createBuyRequest(userId, cash, symbol)
    response = db_rpc.call(request)
    # response['status'] == 400 means they dont have enough money


def handleCommandCommitBuy(args):
    userId = args["userId"]
    transactionNum = args["lineNum"]

    popRequest = databaseFunctions.createPopBuyRequest(userId)
    popResponse = db_rpc.call(popRequest)
    if popResponse["status"] == 200:
        buy = popResponse["body"]
        quote = createQuoteRequest(userId, buy["symbol"], transactionNum)
        quote = quote_rpc.call(quote)
        commitRequest = databaseFunctions.createCommitBuyRequest(userId, buy, quote["value"])
        commitResponse = db_rpc.call(commitRequest)


def handleCommandCancelBuy(args):
    userId = args["userId"]

    request = databaseFunctions.createCancelBuyRequest(userId)
    response = db_rpc.call(request)


def handleCommandSell(args):
    symbol = args["stockSymbol"]
    cash = args["cash"]
    userId = args["userId"]

    request = databaseFunctions.createSellRequest(userId, cash, symbol)
    response = db_rpc.call(request)
    # response['status'] == 400 means they dont have that


def handleCommandCommitSell(args):
    userId = args["userId"]
    transactionNum = args["lineNum"]

    popRequest = databaseFunctions.createPopSellRequest(userId)
    popResponse = db_rpc.call(popRequest)
    if popResponse["status"] == 200:
        sell = popResponse["body"]
        quote = createQuoteRequest(userId, sell["symbol"], transactionNum)
        quote = quote_rpc.call(quote)
        commitRequest = databaseFunctions.createCommitSellRequest(userId, sell, quote["value"])
        commitResponse = db_rpc.call(commitRequest)


def handleCommandCancelSell(args):
    userId = args.get("userId")

    request = databaseFunctions.createCancelSellRequest(userId)
    response = db_rpc.call(request)


def handleCommandSetBuyAmount(args):
    symbol = args.get("stockSymbol")
    amount = args.get("cash")
    userId = args.get("userId")
    transactionNum = args.get("lineNum")

    reserveRequest = databaseFunctions.createReserveCashRequest(userId, amount)
    reserveResponse = db_rpc.call(reserveRequest)
    if reserveResponse["status"] == 200:
        buyRequest = TriggerFunctions.createAddBuyRequest(userId, symbol, amount, transactionNum)
        buyResponse = trigger_rpc.call(buyRequest)


def handleCommandSetBuyTrigger(args):
    symbol = args.get("stockSymbol")
    buyAt = args.get("cash")
    userId = args.get("userId")

    request = TriggerFunctions.createSetBuyActiveRequest(userId, symbol, buyAt)
    response = trigger_rpc.call(request)


def handleCommandCancelSetBuy(args):
    symbol = args["stockSymbol"]
    userId = args["userId"]

    cancelRequest = TriggerFunctions.createCancelBuyRequest(userId, symbol)
    cancelResponse = trigger_rpc.call(cancelRequest)
    if cancelResponse["status"] == 200:
        trigger = cancelResponse["body"]
        releaseRequest = databaseFunctions.createReleaseCashRequest(userId, trigger["cashReserved"])
        releaseResponse = db_rpc.call(releaseRequest)


def handleCommandSetSellAmount(args):
    symbol = args.get("stockSymbol")
    amount = args.get("cash")
    userId = args.get("userId")
    transactionNum = args.get("lineNum")

    sellRequest = TriggerFunctions.createAddSellRequest(userId, symbol, amount, transactionNum)
    sellResponse = trigger_rpc.call(sellRequest)


def handleCommandSetSellTrigger(args):
    symbol = args.get("stockSymbol")
    sellAt = args.get("cash")
    userId = args.get("userId")

    getTriggerRequest = TriggerFunctions.createGetSellRequest(userId, symbol)
    getTriggerResponse = trigger_rpc.call(getTriggerRequest)
    if getTriggerResponse["status"] == 200:
        trigger = getTriggerResponse["body"]
        reserve = math.floor(trigger["maxSellAmount"] / sellAt)

        reservePortfolioRequest = databaseFunctions.createReservePortfolioRequest(userId, reserve, symbol)
        reservePortfolioResponse = db_rpc.call(reservePortfolioRequest)

        if reservePortfolioResponse["status"] == 200:
            setActiveRequest = TriggerFunctions.createSetSellActiveRequest(userId, symbol, sellAt)
            setActiveResponse = trigger_rpc.call(setActiveRequest)


def handleCommandCancelSetSell(args):
    symbol = args.get("stockSymbol")
    userId = args.get("userId")

    cancelTriggerRequest = TriggerFunctions.createCancelSellRequest(userId, symbol)
    cancelTriggerResponse = trigger_rpc.call(cancelTriggerRequest)
    if cancelTriggerResponse["status"] == 200:
        trigger = cancelTriggerResponse["body"]
        if trigger["active"]:
            refund = math.floor(trigger["maxSellAmount"] / trigger["sellAt"])
            releasePortfolioRequest = databaseFunctions.createReleasePortfolioRequest(userId, refund, symbol)
            releasePortfolioResponse = db_rpc.call(releasePortfolioRequest)

def handleCommandDumplog(args):
    requestBody = auditFunctions.createWriteLogs(int(time.time() * 1000), "transactionServer", args["lineNum"],
                                                 args["userId"], args["command"])
    audit_rpc.call(requestBody)


def listenToRabbitQ():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queueNames.WEBSERVER)
    channel.basic_consume(delegate,queue="webserverIn", no_ack=True)
    print "Waiting for requests from queue."
    channel.start_consuming()
    pass


def main():
    listenToRabbitQ()


def incrementSocketNum(socketNum):
    # This is used to increment the socket incase ours is being used
    socketNum += 1
    return socketNum


if __name__ == '__main__':
    print "starting TransactionServer"
    # Global vars
    # -----------------------
    # auditServer = AuditServer()
    # quoteObj = Quotes(auditServer)

    # rpc classes
    audit_rpc = AuditRpcClient()
    quote_rpc = QuoteRpcClient()
    db_rpc = DatabaseRpcClient()
    trigger_rpc = TriggerRpcClient()


    # trigger threads

    # hammerQuoteServerToSell(quoteObj)
    # hammerQuoteServerToBuy(quoteObj)
    # -----------------------

    main()
    # send dumplog
    #
