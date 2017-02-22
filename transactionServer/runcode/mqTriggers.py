import socket
import threading
from threading import Thread
import time
import pika
import json
import queueNames
from mqDatabaseServer import databaseFunctions
import uuid

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
    def createAddBuyRequest(cls, userId, symbol, amount, transactionNumber):
        return {'function': cls.BUY, 'userId': userId, 'symbol': symbol, 'amount': amount, 'transactionNumber': transactionNumber}

    @classmethod
    def createSetBuyActiveRequest(cls, userId, symbol, buyAt):
        return {'function': cls.ACTIVATE_BUY, 'userId': userId, 'symbol': symbol, 'buyAt': buyAt}

    @classmethod
    def createCancelBuyRequest(cls, userId, symbol):
        return {'function': cls.CANCEL_BUY, 'userId': userId, 'symbol': symbol}

    @classmethod
    def createAddSellRequest(cls, userId, symbol, amount, transactionNumber):
        return {'function': cls.SELL, 'userId': userId, 'symbol': symbol, 'amount': amount, 'transactionNumber': transactionNumber}

    @classmethod
    def createSetSellActiveRequest(cls, userId, symbol, sellAt):
        return {'function': cls.ACTIVATE_SELL, 'userId': userId, 'symbol': symbol, 'buyAt': sellAt}

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

    def addBuyTrigger(self, userId, sym, cashReserved, transactionNumber):
        if userId not in self.buyTriggers:
            self.buyTriggers[userId] = {}
        trigger = {"cashReserved": cashReserved, "active": False, "buyAt": 0, "transId": transactionNumber}
        self.buyTriggers[userId][sym] = trigger
        return trigger

    def addSellTrigger(self, userId, sym, maxSellAmount, transactionNumber):
        if userId not in self.sellTriggers:
            self.sellTriggers[userId] = {}
        trigger = {"maxSellAmount": maxSellAmount, "active": False, "sellAt": 0, "transId": transactionNumber}
        self.sellTriggers[userId][sym] = trigger
        return trigger

    def setBuyActive(self, userId, symbol, buyAt):
        if self._triggerExists(userId, symbol, self.buyTriggers):
            trigger = self.buyTriggers.get(symbol).get(userId)
            if buyAt <= trigger.get('cashReserved'):
                trigger["active"] = True
                trigger["buyAt"] = buyAt
                return trigger

    def setSellActive(self, userId, symbol, sellAt):
        if self._triggerExists(userId, symbol, self.sellTriggers):
            trigger = self.sellTriggers.get(symbol).get(userId)
            if sellAt <= trigger.get('cashReserved'):
                trigger["active"] = True
                trigger["sellAt"] = sellAt
                return trigger

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
                    # TODO call for a quote here
                    quote = self.quote.getQuote(symbol, someonesUserId, transId)
                    quoteValue = quote["value"]
                    for userId in triggers.buyTriggers[symbol]:
                        trigger = triggers.buyTriggers[symbol][userId]
                        if trigger["active"]:
                            if quoteValue <= trigger["buyAt"]:
                                # args = {"sym": symbol, "userId": userId, "cash": trigger["maxSellAmount"]}
                                # TODO: this will call db queue to take from reserved
                                buy = databaseFunctions.createBuyRequest(someonesUserId, trigger["maxBuyAmount"] ,symbol)
                                commitBuy = databaseFunctions.createCommitBuyRequest(someonesUserId , buy, quoteValue )
                                db_rpc.call(buy)
                                db_rpc.call(commitBuy)
                                # handleCommandBuy(args)
                                # handleCommandCommitBuy(args)
            time.sleep(1)


class SellTriggerThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.sellLock = threading.Lock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.daemon = True
        self.start()

    def run(self):
        while True:
            if not self.sellLock.locked():
                continue
            for symbol in triggers.buyTriggers:
                if len(triggers.buyTriggers[symbol]):
                    # get the id of someone for the request to the quote server
                    someonesUserId = triggers.sellTriggers[symbol].itervalues().next()
                    transId = triggers.sellTriggers[symbol][someonesUserId]["transId"]
                    # TODO call for a quote here
                    quote = self.quote.getQuote(symbol, someonesUserId, transId)
                    quoteValue = quote["value"]
                    for userId in triggers.sellTriggers[symbol]:
                        trigger = triggers.sellTriggers[symbol][userId]
                        if trigger["active"]:
                            if quoteValue >= trigger["sellAt"]:
                                args = {"sym": symbol, "userId": userId, "cash": trigger["maxSellAmount"]}
                                # TODO: this will call db queue to take from reserved
                                sell = databaseFunctions.createBuyRequest(someonesUserId, trigger["maxSellAmount"],symbol)
                                commitSell = databaseFunctions.createCommitSellRequest(someonesUserId, sell, quoteValue)
                                db_rpc.call(sell)
                                db_rpc.call(commitSell)

            time.sleep(1)


def handleAddBuy(userId, symbol, amount, transactionNumber):
     trigger = triggers.addBuyTrigger(userId, symbol, amount, transactionNumber)
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

def handleAddSell(userId, symbol, amount, transactionNumber):
    trigger = triggers.addSellTrigger(userId, symbol, amount, transactionNumber)
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
    trigger = triggers.localTriggers.getSellTrigger(userId, symbol)
    if trigger:
        return create_response(200, trigger)
    return create_response(400, "trigger doesnt exist")

def on_request(ch, method, props, body):
    payload = json.loads(body)
    function = payload["function"]

    try:
        response = handleFunctionSwitch[function](payload)
    except KeyError:
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


if __name__ == '__main__':
    triggers = Triggers()
    db_rpc = DatabaseRpcClient()
    handleFunctionSwitch = {
        TriggerFunctions.BUY: handleAddBuy,
        TriggerFunctions.ACTIVATE_BUY: handleSetBuyActive,
        TriggerFunctions.CANCEL_BUY: handleCancelBuy,
        TriggerFunctions.SELL: handleAddSell,
        TriggerFunctions.ACTIVATE_SELL: handleSetSellActive,
        TriggerFunctions.CANCEL_SELL: handleCancelSell,
        TriggerFunctions.GET_SELL: handleGetSell
    }

    # BuyTriggerThread()
    # SellTriggerThread()

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queueNames.TRIGGERS)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_request, queue=queueNames.TRIGGERS)

    print("awaiting trigger requests")
    channel.start_consuming()


