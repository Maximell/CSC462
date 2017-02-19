#!/usr/bin/env python
import pika
import time
import json
import queueNames
import math

class databaseFunctions:
    ADD = 1
    BUY = 2
    POP_BUY = 3
    COMMIT_BUY = 4
    CANCEL_BUY = 5
    SELL = 6
    POP_SELL = 7
    COMMIT_SELL = 8
    CANCEL_SELL = 9
    RESERVE_CASH = 10
    RELEASE_CASH = 11
    RESERVE_PORTFOLIO = 12
    RELEASE_PORTFOLIO = 13

    # @classmethod makes it so you dont have to instantiate the class. just call databaseFunctions.createAddRequest()

    @classmethod
    def createAddRequest(cls, userId, amount):
        return {'function': cls.ADD, 'userId': userId, 'amount': amount}

    @classmethod
    def createBuyRequest(cls, userId, amount, symbol):
        return {'function': cls.BUY, 'userId': userId, 'amount': amount, 'symbol': symbol}

    @classmethod
    def createPopBuyRequest(cls, userId):
        return {'function': cls.POP_BUY, 'userId': userId}

    # must be proceeded by popBuyRequest, to obtain the buy - cuz you need to pop -> get quote -> commit
    @classmethod
    def createCommitBuyRequest(cls, userId, buy, costPer):
        return {'function': cls.COMMIT_BUY, 'userId': userId, 'buy': buy, 'costPer': costPer}

    @classmethod
    def createCancelBuyRequest(cls, userId):
        return {'function': cls.CANCEL_BUY, 'userId': userId}

    @classmethod
    def createSellRequest(cls, userId, amount, symbol):
        return {'function': cls.BUY, 'userId': userId, 'amount': amount, 'symbol': symbol}

    @classmethod
    def createPopSellRequest(cls, userId):
        return {'function': cls.POP_SELL, 'userId': userId}

    @classmethod
    def createCommitSellRequest(cls, userId, sell, costPer):
        return {'function': cls.COMMIT_SELL, 'userId': userId, 'sell': sell, 'costPer': costPer}

    @classmethod
    def createCancelSellRequest(cls, userId):
        return {'function': cls.CANCEL_SELL, 'userId': userId}

    @classmethod
    def createReserveCashRequest(cls, userId, amount):
        return {'function': cls.RESERVE_CASH, 'userId': userId, 'amount': amount}

    @classmethod
    def createReleaseCashRequest(cls, userId, amount):
        return {'function': cls.RELEASE_CASH, 'userId': userId, 'amount': amount}

    @classmethod
    def createReservePortfolioRequest(cls, userId, amount, symbol):
        return {'function': cls.RESERVE_PORTFOLIO, 'userId': userId, 'amount': amount, 'symbol': symbol}

    @classmethod
    def createReleasePortfolioRequest(cls, userId, amount, symbol):
        return {'function': cls.RELEASE_PORTFOLIO, 'userId': userId, 'amount': amount, 'symbol': symbol}


    @classmethod
    def listOptions(cls):
        return [attr for attr in dir(databaseFunctions) if not callable(attr) and not attr.startswith("__") and attr != "listOptions" ]


class database:
    def __init__(self, transactionExpire=60):
        self.database = {}
        self.transactionExpire = transactionExpire  # for testing

    def getUser(self, userId):
        return self.database.get(userId)

    def addUser(self, userId):
        if userId not in self.database:
            user = {'userId': userId, 'cash': 0, 'reserve': 0, 'pendingBuys': [], 'pendingSells': [], 'portfolio': {}}
            self.database[userId] = user

            return self.database.get(userId)
        else:
            pass

    # returns user object for success
    # returns None for failure
    def getOrAddUser(self, userId):
        user = self.getUser(userId)
        if user:
            return user
        return self.addUser(userId)

    # returns user object for success
    # returns None for failure
    def addCash(self, userId, amount):
        user = self.database.get(userId)
        if user:
            user['cash'] = user.get('cash') + float(amount)
        else:
            user = {'userId': userId, 'cash': amount, 'reserve': 0}
        self.database[userId] = user
        return self.database.get(userId)

    # returns user object for success
    # returns None for failure
    def reserveCash(self, userId, amount):
        user = self.database.get(userId)
        if not user:
            return 0
        if amount > user.get('cash'):
            return 0
        else:
            user['cash'] = user.get('cash') - amount
            user['reserve'] = amount
            self.database[userId] = user
            return self.database.get(userId)

    # returns user object for success
    # returns None for failure
    def commitReserveCash(self, userId, amount):
        user = self.database.get(userId)
        if not user:
            return 0
        if amount > user.get('reserve'):
            return 0
        else:
            user['reserve'] = user.get('reserve') - amount
            self.database[userId] = user
            return self.database.get(userId)

    # returns user object for success
    # returns None for failure
    def releaseCash(self, userId, amount):
        user = self.database.get(userId)
        if not user:
            return 0
        if amount > user.get('reserve'):
            return 0
        else:
            user['reserve'] = user.get('reserve') - amount
            user['cash'] = user.get('cash') + amount
            self.database[userId] = user
            return self.database.get(userId)

    # returns {symbol, number, costPer, timestamp}
    def pushBuy(self, userId, symbol, number, costPer):
        user = self.getUser(userId)
        if not user:
            return 0
        newBuy = {'symbol': symbol, 'number': number, 'costPer': costPer, 'timestamp': int(time.time())}
        user.get('pendingBuys').append(newBuy)
        return newBuy

    # returns {symbol, number, costPer, timestamp}
    def popBuy(self, userId):
        user = self.getUser(userId)
        if not user:
            return 0
        pendingBuys = user.get('pendingBuys')
        if not len(pendingBuys):
            return 0
        return pendingBuys.pop()

    # returns {symbol, number, costPer, timestamp}
    def pushSell(self, userId, symbol, number, costPer):
        user = self.getUser(userId)
        if not user:
            return 0
        newSell = {'symbol': symbol, 'number': number, 'costPer': costPer, 'timestamp': int(time.time())}
        user.get('pendingSells').append(newSell)
        return newSell

    # returns {symbol, number, costPer, timestamp}
    def popSell(self, userId):
        user = self.getUser(userId)
        if not user:
            return 0
        pendingSells = user.get('pendingSells')
        if not len(pendingSells):
            return 0
        return pendingSells.pop()

    # for testing purposes
    def _checkBuys(self, userId):
        user = self.getUser(userId)
        return user.get('pendingBuys')

    # for testing purposes
    def _checkSells(self, userId):
        user = self.getUser(userId)
        return user.get('pendingSells')

    # returns boolean
    def isBuySellActive(self, buyOrSellObject):
        return (int(buyOrSellObject.get('timestamp', 0)) + self.transactionExpire) > int(time.time())

    # returns remaining amount
    # returns False for error
    def removeFromPortfolio(self, userId, symbol, amount):
        user = self.getUser(userId)
        if not user:
            return False
        portfolio = user.get('portfolio').get(symbol)
        # cant sell portfolio that doesnt exist
        if portfolio is None:
            return False
        portfolioAmount = portfolio.get('amount')
        # trying to sell more than they own
        if portfolioAmount < amount:
            return False

        user['portfolio'][symbol]['amount'] -= amount
        return user['portfolio'][symbol]

    # returns new amount
    # returns False for error
    def addToPortfolio(self, userId, symbol, amount):
        user = self.getUser(userId)
        if not user:
            return False
        portfolio = user.get('portfolio').get(symbol)
        if portfolio is None:
            user['portfolio'][symbol] = {'amount': 0, 'reserved': 0}

        user['portfolio'][symbol]['amount'] = amount
        return user['portfolio'][symbol]

    def reserveFromPortfolio(self, userId, symbol, numberToReserve):
        user = self.getUser(userId)
        if not user:
            return False
        portfolio = user.get('portfolio').get(symbol)
        # cant reserve portfolio that doesnt exist
        if portfolio is None:
            return False
        portfolioAmount = portfolio.get('amount')
        # trying to reserve more than they own
        if portfolioAmount < numberToReserve:
            return False

        user['portfolio'][symbol]['reserved'] += numberToReserve
        user['portfolio'][symbol]['amount'] -= numberToReserve
        return user['portfolio'][symbol]

    def releasePortfolioReserves(self, userId, symbol, numberToRelease):
        user = self.getUser(userId)
        if not user:
            return False
        portfolio = user.get('portfolio').get(symbol)
        # cant reserve portfolio that doesnt exist
        if portfolio is None:
            return False

        portfolioReserved = portfolio.get('reserved')
        if portfolioReserved < numberToRelease:
            return False

        user['portfolio'][symbol]['reserved'] -= numberToRelease
        user['portfolio'][symbol]['amount'] += numberToRelease
        return user['portfolio'][symbol]

    def commitReservedPortfolio(self, userId, symbol, numberToCommit):
        user = self.getUser(userId)
        if not user:
            return False
        portfolio = user.get('portfolio').get(symbol)
        # cant reserve portfolio that doesnt exist
        if portfolio is None:
            return False

        portfolioReserved = portfolio.get('reserved')
        if portfolioReserved < numberToCommit:
            return False

        user['portfolio'][symbol]['reserved'] -= numberToCommit
        return user['portfolio'][symbol]

    def checkPortfolio(self, userId):
        user = self.getUser(userId)
        return user.get('portfolio')


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

def handleAdd(payload):
    amount = payload["amount"]
    userId = payload["userId"]

    user = databaseServer.addCash(userId, amount)
    if user:
        return  create_response(200, user)
    return create_response(500, "unknown error")

def handleBuy(payload):
    symbol = payload["symbol"]
    amount = payload["amount"]
    userId = payload["userId"]

    if databaseServer.getUser(userId)["cash"] >= amount:
        databaseServer.pushBuy(userId, symbol, amount)
        user = databaseServer.reserveCash(userId, amount)
        return create_response(200, user)
    else:
        return create_response(400, "not enough money available")

def handlePopBuy(payload):
    userId = payload["userId"]

    buy = databaseServer.popBuy(userId)
    if buy:
        return create_response(200, buy)
    return create_response(400, "no buys available")

def handleCommitBuy(payload):
    userId = payload["userId"]
    buy = payload["buy"]
    costPer = payload["costPer"]
    symbol = buy["symbol"]
    moneyReserved = buy["amount"]

    if databaseServer.isBuySellActive(buy):
        numberOfStocks = math.floor(moneyReserved / costPer)

        databaseServer.addToPortfolio(userId, symbol, numberOfStocks)

        spentCash = numberOfStocks * costPer
        unspentCash = moneyReserved - spentCash

        databaseServer.commitReserveCash(userId, numberOfStocks * costPer)
        user = databaseServer.releaseCash(userId, unspentCash)
        return create_response(200, user)
    else:
        databaseServer.releaseCash(userId, moneyReserved)
        return create_response(400, "buy no longer active")

def handleCancelBuy(payload):
    userId = payload["userId"]
    buy = databaseServer.popBuy(userId)
    if buy:
        user = databaseServer.releaseCash(userId, buy["amount"])
        return create_response(200, user)

    return create_response(400, "no buys available")

def handleSell(payload):
    symbol = payload["symbol"]
    amount = payload["amount"]
    userId = payload["userId"]

    if databaseServer.pushSell(userId, symbol, amount):
        return create_response(200, databaseServer.getUser(userId))
    return create_response(400, "dont own any of those stock")

def handlePopSell(payload):
    userId = payload["userId"]

    sell = databaseServer.popSell(userId)
    if sell:
        return create_response(200, sell)
    return create_response(400, "no sells available")

def handleCommitSell(payload):
    userId = payload["userId"]
    sell = payload["sell"]
    costPer = payload["costPer"]
    symbol = sell["symbol"]
    amount = sell["amount"]

    if databaseServer.isBuySellActive(sell):
        numberOfStocks = math.floor(amount / costPer)

        databaseServer.removeFromPortfolio(userId, symbol, numberOfStocks)
        user = databaseServer.addCash(userId, numberOfStocks * costPer)
        return create_response(200, user)
    return create_response(400, "sell no longer active")

def handleCancelSell(payload):
    userId = payload["userId"]

    sell = databaseServer.popSell(userId)
    if sell:
        return create_response(200, databaseServer.getUser(userId))
    return create_response(400, "no sells available")

def handleReserveCash(payload):
    amount = payload["amount"]
    userId = payload["userId"]

    user = databaseServer.reserveCash(userId, amount)
    return create_response(200, user)

def handleReleaseCash(payload):
    amount = payload["amount"]
    userId = payload["userId"]

    user = databaseServer.releaseCash(userId, amount)
    return create_response(200, user)

def handleReservePortfolio(payload):
    symbol = payload["symbol"]
    amount = payload["amount"]
    userId = payload["userId"]

    user = databaseServer.reserveFromPortfolio(userId, symbol, amount)
    return create_response(200, user)

def handleReleasePortfolio(payload):
    symbol = payload["symbol"]
    amount = payload["amount"]
    userId = payload["userId"]

    user = databaseServer.releasePortfolioReserves(userId, symbol, amount)
    return create_response(200, user)


if __name__ == '__main__':
    databaseServer = database()

    handleFunctionSwitch = {
        databaseFunctions.ADD: handleAdd,
        databaseFunctions.BUY: handleBuy,
        databaseFunctions.POP_BUY: handlePopBuy,
        databaseFunctions.COMMIT_BUY: handleCommitBuy,
        databaseFunctions.CANCEL_BUY: handleCancelBuy,
        databaseFunctions.SELL: handleSell,
        databaseFunctions.POP_SELL: handlePopSell,
        databaseFunctions.COMMIT_SELL: handleCommitSell,
        databaseFunctions.CANCEL_SELL: handleCancelSell,
        databaseFunctions.RESERVE_CASH: handleReserveCash,
        databaseFunctions.RELEASE_CASH: handleReleaseCash,
        databaseFunctions.RESERVE_PORTFOLIO: handleReservePortfolio,
        databaseFunctions.RELEASE_PORTFOLIO: handleReleasePortfolio
    }

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queueNames.DATABASE)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_request, queue=queueNames.DATABASE)

    print("awaiting database requests")
    channel.start_consuming()