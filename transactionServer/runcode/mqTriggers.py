import socket
import threading
import time
import json
import math
from threading import Thread
from rabbitMQSetups import RabbitMQClient, RabbitMQReceiver
from mqDatabaseServer import databaseFunctions
from mqQuoteServer import createQuoteRequest
import Queue


import multiprocessing
from multiprocessing import Process


class rabbitConsumer():
    def __init__(self, queueName,Q1, Q2, Q3):
        self.rabbitPQueue1 = Q1
        self.rabbitPQueue2 = Q2
        self.rabbitPQueue3 = Q3
        print "initialize queues"
        self.connection = RabbitMQReceiver(self.consume, queueName)
        print "connectionb done"

    def consume(self, ch, method, props, body):
        payload = json.loads(body)
        print "Reciveed :", payload

        line = payload.get("lineNum")
        if line is None:
            line = payload.get("transactionNum")
        print "trying to put in QUEUE"
        if props.priority == 1:
            # flipping priority b/c Priority works lowestest to highest
            # But our system works the other way.

            # We need to display lineNum infront of payload to so get() works properly
            self.rabbitPQueue1.put((1, [line, payload]))
        elif props.priority == 2:
            self.rabbitPQueue2.put((2, [line, payload]))
        else:
            self.rabbitPQueue3.put((3, [line, payload]))
        print "put in queue"


class TriggerFunctions:
    BUY = 1
    ACTIVATE_BUY = 2
    CANCEL_BUY = 3
    SELL = 4
    ACTIVATE_SELL = 5
    CANCEL_SELL = 6
    GET_SELL = 7
    QUOTE = 8

    @classmethod
    def createAddBuyRequest(cls, command, userId, stockSymbol, amount, lineNum):
        return {
            'function': cls.BUY,
            'command': command,
            'userId': userId,
            'stockSymbol': stockSymbol,
            'cash': amount,
            'lineNum': lineNum,
        }

    @classmethod
    def createSetBuyActiveRequest(cls, command, userId, symbol, buyAt, lineNum):
        return {
            'function': cls.ACTIVATE_BUY,
            'command': command,
            'userId': userId,
            'stockSymbol': symbol,
            'cash': buyAt,
            'lineNum': lineNum,
        }

    @classmethod
    def createCancelBuyRequest(cls, command, userId, symbol, lineNum):
        return {
            'function': cls.CANCEL_BUY,
            'command': command,
            'userId': userId,
            'stockSymbol': symbol,
            'lineNum': lineNum,
        }

    @classmethod
    def createAddSellRequest(cls, command, userId, symbol, amount, lineNum):
        return {
            'function': cls.SELL,
            'command': command,
            'userId': userId,
            'stockSymbol': symbol,
            'cash': amount,
            'lineNum': lineNum,
        }

    @classmethod
    def createSetSellActiveRequest(cls, command, userId, symbol, sellAt, lineNum):
        return {
            'function': cls.ACTIVATE_SELL,
            'command': command,
            'userId': userId,
            'stockSymbol': symbol,
            'cash': sellAt,
            'lineNum': lineNum,
        }

    @classmethod
    def createCancelSellRequest(cls, command, userId, symbol, lineNum):
        return {
            'function': cls.CANCEL_SELL,
            'command': command,
            'userId': userId,
            'stockSymbol': symbol,
            'lineNum': lineNum,
        }

    @classmethod
    def createGetSellRequest(cls, command, userId, symbol, cash, lineNum):
        return {
            'function': cls.GET_SELL,
            'command': command,
            'userId': userId,
            'stockSymbol': symbol,
            'cash': cash,
            'lineNum': lineNum,
        }

    @classmethod
    def listOptions(cls):
        return [attr for attr in dir(databaseFunctions) if not callable(attr) and not attr.startswith("__") and attr != "listOptions" ]


class Triggers:
    def __init__(self):
        self.buyTriggers = {}
        self.sellTriggers = {}

    def getBuyTriggers(self):
        return self.buyTriggers

    def getBuyTrigger(self, userId, symbol):
        if self._triggerExists(userId, symbol, self.buyTriggers):
            return self.buyTriggers[symbol][userId]

    def getSellTriggers(self):
        return self.sellTriggers

    def getSellTrigger(self, userId, symbol):
        if self._triggerExists(userId, symbol, self.sellTriggers):
            return self.sellTriggers[symbol][userId]

    def addBuyTrigger(self, userId, sym, cashReserved, transactionNum):
        if sym not in self.buyTriggers:
            self.buyTriggers[sym] = {}
        trigger = {"cashReserved": cashReserved, "active": False, "buyAt": 0, "transId": transactionNum}
        self.buyTriggers[sym][userId] = trigger
        return trigger

    def addSellTrigger(self, userId, sym, maxSellAmount, transactionNum):
        if sym not in self.sellTriggers:
            self.sellTriggers[sym] = {}
        trigger = {"maxSellAmount": maxSellAmount, "active": False, "sellAt": 0, "transId": transactionNum}
        self.sellTriggers[sym][userId] = trigger
        return trigger

    def setBuyActive(self, userId, symbol, buyAt):
        if self._triggerExists(userId, symbol, self.buyTriggers):
            trigger = self.buyTriggers.get(symbol).get(userId)
            if buyAt <= trigger['cashReserved']:
                trigger["active"] = True
                trigger["buyAt"] = buyAt
                return trigger
            else:
                print "not enough in cashReserved"

    def setSellActive(self, userId, symbol, sellAt):
        if self._triggerExists(userId, symbol, self.sellTriggers):
            trigger = self.sellTriggers.get(symbol).get(userId)
            # TODO: take deeper look at this logic, it might be backwards?
            # sell 500 worth of X, sellAt 300 each. should be good
            # sell 500 worth of X, sell at 600 each. not good?
            # just switched it, until march 5th, it was sellAt >= trigger['maxSellAmount']
            if sellAt <= trigger['maxSellAmount']:
                trigger["active"] = True
                trigger["sellAt"] = sellAt
                return trigger
            else:
                print "sellAt greater than maxSellAmount"

    def cancelBuyTrigger(self, userId, symbol):
        # danger here'
        if self._triggerExists(userId, symbol, self.buyTriggers):
            buyThread.buyLock.acquire()
            removedTrigger = self.buyTriggers[symbol][userId]
            del self.buyTriggers[symbol][userId]
            buyThread.buyLock.release()
            return removedTrigger

    def cancelSellTrigger(self, userId, symbol):
        # danger here
        if self._triggerExists(userId, symbol, self.sellTriggers):
            sellThread.sellLock.acquire()
            removedTrigger = self.sellTriggers[symbol][userId]
            del self.sellTriggers[symbol][userId]
            sellThread.sellLock.release()
            return removedTrigger

    def _triggerExists(self, userId, symbol, triggers):
        # print triggers
        # print userId
        # print symbol
        # print triggers.get(userId, {}).get(userId)
        return bool(triggers.get(symbol, {}).get(userId))


# quote shape: symbol: {value: string, retrieved: epoch time, user: string, cryptoKey: string}
class Quotes():
    def __init__(self, cacheExpire=60):
        self.cacheExpire = cacheExpire
        self.quoteCache = {}

    def getQuote(self, symbol):
        cache = self.quoteCache.get(symbol)
        if cache:
            if self._cacheIsActive(cache):
                return cache
        return None

    def cacheQuote(self, symbol, retrieved, value):
        self.quoteCache[symbol] = {"retrieved": retrieved, "value": value}

    def _cacheIsActive(self, quote):
        return (int(quote.get('retrieved', 0)) + self.cacheExpire) > int(time.time())


class BuyTriggerThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.buyLock = threading.Lock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.daemon = True
        self.start()

    def run(self):
        while True:
            if not self.buyLock.locked():
                continue
            for symbol in triggers.buyTriggers:
                if len(triggers.buyTriggers[symbol]):
                    # get the id of someone for the request to the quote server
                    someonesUserId = triggers.buyTriggers[symbol].itervalues().next()
                    transId = triggers.buyTriggers[symbol][someonesUserId]["transId"]

                    # essentially a stop and wait RPC
                    quote = quotesCache.getQuote(symbol)
                    if quote is None:
                        # tells quote client where to return to
                        args = {"trans": RabbitMQClient.TRIGGERS}
                        quoteClient.send(
                            createQuoteRequest(someonesUserId, symbol, transId, args)
                        )
                        while quote is None:
                            # .1 is a guess? better interval to sleep?
                            time.sleep(0.1)
                            quote = quotesCache.getQuote(symbol)

                    quoteValue = quote["value"]
                    for userId in triggers.buyTriggers[symbol]:
                        trigger = triggers.buyTriggers[symbol][userId]
                        if trigger["active"]:
                            if quoteValue <= trigger["buyAt"]:
                                portfolioAmount = math.floor(trigger["cashReserved"] / quoteValue)
                                cashCommitAmount = portfolioAmount * quoteValue
                                cashReleaseAmount = trigger["cashReserved"] - cashCommitAmount

                                databaseClient.send(
                                    databaseFunctions.createBuyTriggerRequest(
                                        userId,
                                        cashCommitAmount,
                                        cashReleaseAmount,
                                        portfolioAmount,
                                        symbol
                                    )
                                )
                                triggers.cancelBuyTrigger(userId, symbol)

            time.sleep(50)


class SellTriggerThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.sellLock = threading.Lock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.daemon = True
        self.start()

    def run(self):
        # offset buy and sell triggers by 5 seconds
        time.sleep(5)
        while True:
            if not self.sellLock.locked():
                continue
            for symbol in triggers.buyTriggers:
                if len(triggers.buyTriggers[symbol]):
                    # get the id of someone for the request to the quote server
                    someonesUserId = triggers.sellTriggers[symbol].itervalues().next()
                    transId = triggers.sellTriggers[symbol][someonesUserId]["transId"]

                    # essentially a stop and wait RPC
                    quote = quotesCache.getQuote(symbol)
                    if quote is None:
                        # tells quote client where to return to
                        args = {"trans": RabbitMQClient.TRIGGERS}
                        quoteClient.send(
                            createQuoteRequest(someonesUserId, symbol, transId, args)
                        )
                        while quote is None:
                            # .1 is a guess? better interval to sleep?
                            time.sleep(.1)
                            quote = quotesCache.getQuote(symbol)

                    quoteValue = quote["value"]
                    for userId in triggers.sellTriggers[symbol]:
                        trigger = triggers.sellTriggers[symbol][userId]
                        if trigger["active"]:
                            if quoteValue >= trigger["sellAt"]:
                                portfolioCommitAmount = math.floor(trigger["maxSellAmount"] / quoteValue)
                                portfolioReleaseAmount = math.floor(trigger["maxSellAmount"] / trigger["sellAt"]) - portfolioCommitAmount

                                databaseClient.send(
                                    databaseFunctions.createSellTriggerRequest(
                                        userId,
                                        quoteValue,
                                        portfolioCommitAmount,
                                        portfolioReleaseAmount,
                                        symbol
                                    )
                                )

                                triggers.cancelSellTrigger(userId, symbol)

            time.sleep(50)


def handleAddBuy(payload):
    userId = payload["userId"]
    symbol = payload["stockSymbol"]
    amount = payload["cash"]
    transactionNum = payload["lineNum"]

    trigger = triggers.addBuyTrigger(userId, symbol, amount, transactionNum)
    if trigger:
        payload['response'] = 200
        payload['trigger'] = trigger
    else:
        payload['response'] = 500
        payload['errorString'] = "unknown error"
    return payload


def handleSetBuyActive(payload):
    userId = payload["userId"]
    symbol = payload["stockSymbol"]
    buyAt = payload["cash"]

    trigger = triggers.setBuyActive(userId, symbol, buyAt)
    if trigger:
        payload['response'] = 200
        payload['trigger'] = trigger
    else:
        payload['response'] = 400
        payload['errorString'] = "trigger doesnt exist or buyAt is higher then cash amount reserved"
    return payload


def handleCancelBuy(payload):
    userId = payload["userId"]
    symbol = payload["stockSymbol"]

    trigger = triggers.cancelBuyTrigger(userId, symbol)
    if trigger:
        payload['response'] = 200
        payload['trigger'] = trigger
    else:
        payload['response'] = 400
        payload['errorString'] = "trigger doesnt exist"
    return payload


def handleAddSell(payload):
    userId = payload["userId"]
    symbol = payload["stockSymbol"]
    amount = payload["cash"]
    transactionNum = payload["lineNum"]

    trigger = triggers.addSellTrigger(userId, symbol, amount, transactionNum)
    if trigger:
        payload['response'] = 200
        payload['trigger'] = trigger
    else:
        payload['response'] = 500
        payload['errorString'] = "unknown error"
    return payload


def handleSetSellActive(payload):
    userId = payload["userId"]
    symbol = payload["stockSymbol"]
    sellAt = payload["cash"]

    trigger = triggers.setSellActive(userId, symbol, sellAt)
    if trigger:
        payload['response'] = 200
        payload['trigger'] = trigger
    else:
        payload['response'] = 400
        payload['errorString'] = "trigger doesnt exist or sellAt is greater then max"
    return payload


def handleCancelSell(payload):
    userId = payload["userId"]
    symbol = payload["stockSymbol"]

    trigger = triggers.cancelSellTrigger(userId, symbol)
    if trigger:
        payload['response'] = 200
        payload['trigger'] = trigger
    else:
        payload['response'] = 400
        payload['errorString'] = "trigger doesnt exist"
    return payload


def handleGetSell(payload):
    userId = payload["userId"]
    symbol = payload["stockSymbol"]

    trigger = triggers.getSellTrigger(userId, symbol)
    if trigger:
        payload['response'] = 200
        payload['sellTrigger'] = trigger
    else:
        payload['response'] = 400
        payload['errorString'] = "trigger doesnt exist"
    return payload

def handleQuote(payload):
    print "quote payload:", payload

    symbol = payload["stockSymbol"]
    quoteVal = payload["quote"]
    retrieved = payload["quoteRetrieved"]

    quotesCache.cacheQuote(symbol, retrieved, quoteVal)

    return DONT_RETURN_TO_TRANSACTION



def on_request(ch, method, props, payload):
    print "payload: ", payload

    function = handleFunctionSwitch.get(payload["function"])
    if function:
        response = function(payload)
    else:
        payload['response'] = 404
        payload['errorString'] = "function not found"
        response = payload

    if response != DONT_RETURN_TO_TRANSACTION:
        transactionClient.send(response)


def create_error_response(status, response):
    return {'response': status, 'errorString': response}


if __name__ == '__main__':
    DONT_RETURN_TO_TRANSACTION = "dontReturn"

    triggers = Triggers()
    quotesCache = Quotes()

    handleFunctionSwitch = {
        TriggerFunctions.BUY: handleAddBuy,
        TriggerFunctions.ACTIVATE_BUY: handleSetBuyActive,
        TriggerFunctions.CANCEL_BUY: handleCancelBuy,
        TriggerFunctions.SELL: handleAddSell,
        TriggerFunctions.ACTIVATE_SELL: handleSetSellActive,
        TriggerFunctions.CANCEL_SELL: handleCancelSell,
        TriggerFunctions.GET_SELL: handleGetSell,
        TriggerFunctions.QUOTE: handleQuote,
    }

    # self.start() currently commented out in both threads
    buyThread = BuyTriggerThread()
    sellThread = SellTriggerThread()

    transactionClient = RabbitMQClient(RabbitMQClient.TRANSACTION)
    quoteClient = RabbitMQClient(RabbitMQClient.QUOTE)
    databaseClient = RabbitMQClient(RabbitMQClient.DATABASE)


    print("awaiting trigger requests")


    P1Q_rabbit = multiprocessing.Queue()
    P2Q_rabbit = multiprocessing.Queue()
    P3Q_rabbit = multiprocessing.Queue()

    print "Created multiprocess PriorityQueues"
    consumer_process = Process(target=rabbitConsumer,
                               args=(RabbitMQReceiver.TRIGGERS, P1Q_rabbit, P2Q_rabbit, P3Q_rabbit))
    consumer_process.start()
    print "Created multiprocess Consummer"

    while (True):
        try:
            msg = P2Q_rabbit.get(False)
            if msg:
                payload = msg[1]
                args = payload[1]
                props = msg[0]
                print "queue size: ", P2Q_rabbit.qsize()
                on_request(None, None, props, args)
            continue
        except:
            pass
            try:
                msg = P1Q_rabbit.get(False)
                if msg:
                    payload = msg[1]
                    args = payload[1]
                    props = msg[0]
                    print "queue size: ", P1Q_rabbit.qsize()
                    on_request(None, None, props, args)
                continue
            except:
                try:
                    msg = P3Q_rabbit.get(False)
                    if msg:
                        payload = msg[1]
                        args = payload[1]
                        props = msg[0]
                        print "queue size: ", P3Q_rabbit.qsize()
                        on_request(None, None, props, args)
                    continue
                except:
                    pass


