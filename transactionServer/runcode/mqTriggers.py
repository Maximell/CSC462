import socket
import threading
import time
import pika
import json
import uuid
import math
from threading import Thread
from rabbitMQClient import RabbitMQClient
from mqDatabaseServer import databaseFunctions
from mqQuoteServer import createQuoteRequest

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
            routing_key=RabbitMQClient.DATABASE,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body=json.dumps(requestBody)
        )
        while self.response is None:
            self.connection.process_data_events()
        return self.response


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
            routing_key=RabbitMQClient.QUOTE,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body=json.dumps(requestBody)
        )
        while self.response is None:
            self.connection.process_data_events()
        return self.response


class TriggerFunctions:
    BUY = 1
    ACTIVATE_BUY = 2
    CANCEL_BUY = 3
    SELL = 4
    ACTIVATE_SELL = 5
    CANCEL_SELL = 6
    GET_SELL = 7

    @classmethod
    def createAddBuyRequest(cls, userId, symbol, amount, transactionNum):
        return {'function': cls.BUY, 'userId': userId, 'symbol': symbol, 'amount': amount, 'transactionNum': transactionNum}

    @classmethod
    def createSetBuyActiveRequest(cls, userId, symbol, buyAt):
        return {'function': cls.ACTIVATE_BUY, 'userId': userId, 'symbol': symbol, 'buyAt': buyAt}

    @classmethod
    def createCancelBuyRequest(cls, userId, symbol):
        return {'function': cls.CANCEL_BUY, 'userId': userId, 'symbol': symbol}

    @classmethod
    def createAddSellRequest(cls, userId, symbol, amount, transactionNum):
        return {'function': cls.SELL, 'userId': userId, 'symbol': symbol, 'amount': amount, 'transactionNum': transactionNum}

    @classmethod
    def createSetSellActiveRequest(cls, userId, symbol, sellAt):
        return {'function': cls.ACTIVATE_SELL, 'userId': userId, 'symbol': symbol, 'sellAt': sellAt}

    @classmethod
    def createCancelSellRequest(cls, userId, symbol):
        return {'function': cls.CANCEL_SELL, 'userId': userId, 'symbol': symbol}

    @classmethod
    def createGetSellRequest(cls, userId, symbol):
        return {'function': cls.GET_SELL, 'userId': userId, 'symbol': symbol}

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
            if sellAt >= trigger['maxSellAmount']:
                trigger["active"] = True
                trigger["sellAt"] = sellAt
                return trigger
            else:
                print "sellat less than maxSellAmount"

    def cancelBuyTrigger(self, userId, symbol):
        # danger here'
        if self._triggerExists(userId, symbol, self.buyTriggers):
            BuyTriggerThread.buyLock.acquire()
            removedTrigger = self.buyTriggers[symbol][userId]
            del self.buyTriggers[symbol][userId]
            BuyTriggerThread.buyLock.realease()
            return removedTrigger

    def cancelSellTrigger(self, userId, symbol):
        # danger here
        if self._triggerExists(userId, symbol, self.sellTriggers):
            SellTriggerThread.sellLock.acquire()
            removedTrigger = self.sellTriggers[symbol][userId]
            del self.sellTriggers[symbol][userId]
            SellTriggerThread.sellLock.realease()
            return removedTrigger

    def _triggerExists(self, userId, symbol, triggers):
        # print triggers
        # print userId
        # print symbol
        # print triggers.get(userId, {}).get(userId)
        return bool(triggers.get(symbol, {}).get(userId))


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
                    quote = quote_rpc.call(
                        createQuoteRequest(someonesUserId, symbol, transId)
                    )
                    quoteValue = quote["value"]
                    for userId in triggers.buyTriggers[symbol]:
                        trigger = triggers.buyTriggers[symbol][userId]
                        if trigger["active"]:
                            if quoteValue <= trigger["buyAt"]:
                                portfolioAmount = math.floor(trigger["cashReserved"] / quoteValue)
                                cashCommitAmount = portfolioAmount * quoteValue
                                cashReleaseAmount = trigger["cashReserved"] - cashCommitAmount
                                request = databaseFunctions.createBuyTriggerRequest(userId, cashCommitAmount, cashReleaseAmount, portfolioAmount, symbol)
                                db_rpc.call(request)

            time.sleep(15)


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
                    quote = quote_rpc.call(
                        createQuoteRequest(someonesUserId, symbol, transId)
                    )
                    quoteValue = quote["value"]
                    for userId in triggers.sellTriggers[symbol]:
                        trigger = triggers.sellTriggers[symbol][userId]
                        if trigger["active"]:
                            if quoteValue >= trigger["sellAt"]:
                                portfolioCommitAmount = math.floor(trigger["maxSellAmount"] / quoteValue)
                                portfolioReleaseAmount = math.floor(trigger["maxSellAmount"] / trigger["sellAt"]) - portfolioCommitAmount
                                request = databaseFunctions.createSellTriggerRequest(
                                    userId,
                                    quoteValue,
                                    portfolioCommitAmount,
                                    portfolioReleaseAmount,
                                    symbol
                                )
                                db_rpc.call(request)

            time.sleep(15)


def handleAddBuy(userId, symbol, amount, transactionNum):
     trigger = triggers.addBuyTrigger(userId, symbol, amount, transactionNum)
     if trigger:
         return create_response(200, trigger)
     return create_response(400, "bad request")

def handleSetBuyActive(userId, symbol, buyAt):
    trigger = triggers.setBuyActive(userId, symbol, buyAt)
    if trigger:
        return create_response(200, trigger)
    return create_response(400, "trigger doesnt exist")

def handleCancelBuy(userId, symbol):
    trigger = triggers.cancelBuyTrigger(userId, symbol)
    if trigger:
        return create_response(200, trigger)
    return create_response(400, "trigger doesnt exist")

def handleAddSell(userId, symbol, amount, transactionNum):
    trigger = triggers.addSellTrigger(userId, symbol, amount, transactionNum)
    if trigger:
        return create_response(200, trigger)
    return create_response(400, "bad request")

def handleSetSellActive(userId, symbol, sellAt):
    trigger = triggers.setSellActive(userId, symbol, sellAt)
    if trigger:
        return create_response(200, trigger)
    return create_response(400, "trigger doesnt exist or is at a higher value than amount reserved for it")

def handleCancelSell(userId, symbol):
    trigger = triggers.cancelSellTrigger(userId, symbol)
    if trigger:
        return create_response(200, trigger)
    return create_response(400, "trigger doesnt exist")

def handleGetSell(userId, symbol):
    trigger = triggers.getSellTrigger(userId, symbol)
    if trigger:
        return create_response(200, trigger)
    return create_response(400, "trigger doesnt exist")

def on_request(ch, method, props, body):
    payload = json.loads(body)
    function = payload["function"]
    del payload["function"]

    try:
        response = handleFunctionSwitch[function](**payload)
    except KeyError:
        print "404 error at:", function, payload
        response = create_response(404, "function not found")

    response = json.dumps(response)

    ch.basic_publish(
        exchange='',
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body=response
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)


def create_response(status, response):
    return {'status': status, 'body': response}


# if __name__ == '__main__':
#     triggers = Triggers()
#
#     handleFunctionSwitch = {
#         TriggerFunctions.BUY: handleAddBuy,
#         TriggerFunctions.ACTIVATE_BUY: handleSetBuyActive,
#         TriggerFunctions.CANCEL_BUY: handleCancelBuy,
#         TriggerFunctions.SELL: handleAddSell,
#         TriggerFunctions.ACTIVATE_SELL: handleSetSellActive,
#         TriggerFunctions.CANCEL_SELL: handleCancelSell,
#         TriggerFunctions.GET_SELL: handleGetSell
#     }
#
#     quote_rpc = QuoteRpcClient()
#     db_rpc = DatabaseRpcClient()
#
#     BuyTriggerThread()
#     SellTriggerThread()
#
#     connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
#     channel = connection.channel()
#     channel.queue_declare(queue=queueNames.TRIGGERS)
#     channel.basic_qos(prefetch_count=1)
#     channel.basic_consume(on_request, queue=queueNames.TRIGGERS)
#
#     print("awaiting trigger requests")
#     channel.start_consuming()


