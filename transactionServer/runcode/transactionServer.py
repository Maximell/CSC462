# demonstrate talking to the quote server
import math
import socket
import threading
from threading import Thread
import time
import urlparse
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import BaseServer
from random import randint
import uuid
import pika
import json
import queueNames
from mqDatabaseServer import databaseFunctions
from mqQuoteServer import createQuoteRequest
from mqTriggers import TriggerFunctions
from mqAuditServer import auditFunctions

from OpenSSL import SSL
import ast


# from events import Event



# COMMANDS NEEDED
#
# add
#
# quote j
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
#
# dumplog    (x2)
# display_summary

# general structure of endpoints
# Add:
#   databaseServer.getOrAddUser
#
# Quote:
#   quotes.getQuote
#
# Buy:
#   quotes.getQuote
#   databaseServer.pushBuy
#   databaseServer.reserveCash
#
# Cancel buy:
#   databaseServer.popBuy
#   databaseServer.releaseCash
#
# Commit buy:
#   databaseServer.popBuy
#   databaseServer.isBuySellActive
#   databaseServer.addToPortfolio
#   databaseServer.missingFunctionForTakeCash
#
# Sell:
# quotes.getQuote
#   databaseServer.pushSell
#
# Cancel Sell:
#   databaseServer.popSell
#
# commit Sell:
#   databaseServer.popSell
#   databaseServer.isBuySellActive
#   databaseServer.removeFromPortfolio
#   databaseServer.addCash

#
# class events:
#     systemEvent
#     accountTransaction
#     commandEvent - this adds a method for each type of command
#         userCommand
#         quoteServer
#         errorEvent
#
# method add arguments

# Class for a logging 'server'
# In general, an event takes the form of:
#   event = {
#       'type': 'someType',
#           userCommand
#           accountTransaction
#           systemEvent
#           quoteServer
#           errorEvent
#       'timestamp': seconds since the epoch,
#       'server': 'where the server originated from',
#       'transactionNum': the transaction number the event is associated with,
#       'username': 'userId of the user who triggered the event'
#       'args': {} Some dictionary - specific for the type of event.
#   }
#   Valid 'type's and their arg values:
#       userCommand
#           args: {
#               'command': {'name': ,
#                           args{}}'string representing the user's command',
#                   add
#                   commit_buy
#                   cancel_buy
#                   commit_sell
#                   cancel_sell
#                   display_summary
#                       no additional args
#
#                   quote
#                   buy
#                   sell
#                   set_buy_amount
#                   cancel_set_buy
#                   set_buy_trigger
#                   set_sell_amount
#                   set_sell_trigger
#                   cancel_set_sell
#                       need stockSymbol
#
#                   dumplog
#                       fileName
#
#                   add
#                   buy
#                   sell
#                   set_buy_amount
#                   set_buy_trigger
#                   set_sell_amount
#                   set_sell_trigger
#                       funds
#           }
#       accountTransaction
#           args: {
#               'action': string corresponding to type of account transaction
#                   add
#                   remove
#                   reserve
#                   free
#               'funds': amount of money being moved
#           }
#       systemEvent
#           args: {
#               'command': same as in userCommand
#           }
#       quoteServer
#           args: {
#               'quoteServerTime': time the quote was received from the quote server,
#               'stockSymbol': 'stcksymbl',
#               'price': price of the stock at the time the server quoted it,
#               'cryptokey': 'cryptographic key the server returns'
#           }
#       errorEvent
#           args: {
#               'command': same as in userCommand,
#               'errorMessage': message associated with the error
#           }
class AuditServer:
    def __init__(self):
        self.logFile = []


    # TODO: need a logAdminCommand which doesnt have userId (for dumplog command)
    def logUserCommand(self, timeStamp, server, transactionNum, userId, commandName, stockSymbol=None, fileName=None, amount=None):
        dictionary = {
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'commandName': commandName,
            'logType': 'userCommand'
        }
        if stockSymbol:
            dictionary = dict(dictionary, stockSymbol=stockSymbol)
        if fileName:
            dictionary = dict(dictionary, fileName=fileName)
        if amount:
            dictionary = dict(dictionary, amount=amount)
        self.logFile.append(dictionary)

    def logQuoteServer(self, timeStamp, server, transactionNum, userId, quoteServerTime, stockSymbol, price, cryptoKey):
        dictionary = {
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'logType': 'quoteServer',
            'quoteServerTime': quoteServerTime,
            'stockSymbol': stockSymbol,
            'price': price,
            'cryptoKey': cryptoKey
        }
        self.logFile.append(dictionary)

    def logAccountTransaction(self, timeStamp, server, transactionNum, userId, commandName, action, funds):
        dictionary = {
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'logType': 'accountTransaction',
            'action': action,
            'funds': funds
        }
        self.logFile.append(dictionary)

    def logSystemEvent(self, timeStamp, server, transactionNum, userId, commandName, stockSymbol=None, fileName=None, amount=None):
        dictionary = {
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'commandName': commandName,
            'logType': 'systemEvent'
        }
        if stockSymbol:
            dictionary = dict(dictionary, stockSymbol=stockSymbol)
        if fileName:
            dictionary = dict(dictionary, fileName=fileName)
        if amount:
            dictionary = dict(dictionary, amount=amount)
        self.logFile.append(dictionary)

    def logErrorMessage(self, timeStamp, server, transactionNum, userId, commandName, errorMessage):
        dictionary = {
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'commandName': commandName,
            'logType': 'errorEvent',
            'errorMessage': errorMessage
        }
        self.logFile.append(dictionary)

    def logDebugMessage(self, timeStamp, server, transactionNum, userId, commandName, debugMessage):
        dictionary = {
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'commandName': commandName,
            'logType': 'debugEvent',
            'debugMessage': debugMessage
        }
        self.logFile.append(dictionary)

    # def logUserCommand(self, **kwargs):
    #     self.logFile.append(dict(kwargs,
    #                              logType='userCommand'
    #                              ))

    def writeLogs(self, fileName):
        self._dumpIntoFile(fileName)

    # dumps the logs to a given file
    def _dumpIntoFile(self, fileName):
        try:
            file = open(fileName, 'w')
        except IOError:
            print 'Attempted to save into file %s but couldn\'t open file for writing.' % (fileName)

        file.write('<?xml version="1.0"?>\n')
        file.write('<log>\n\n')
        for log in self.logFile:
            logType = log['logType']
            file.write('\t<' + logType + '>\n')
            file.write('\t\t<timestamp>' + str(log['timeStamp']) + '</timestamp>\n')
            file.write('\t\t<server>' + str(log['server']) + '</server>\n')
            file.write('\t\t<transactionNum>' + str(log['transactionNum']) + '</transactionNum>\n')
            file.write('\t\t<username>' + str(log['userId']) + '</username>\n')
            if logType == 'userCommand':
                file.write('\t\t<command>' + str(log['commandName']) + '</command>\n')
                if log.get('stockSymbol'):
                    file.write('\t\t<stockSymbol>' + str(log['stockSymbol']) + '</stockSymbol>\n')
                if log.get('fileName'):
                    file.write('\t\t<filename>' + str(log['fileName']) + '</filename>\n')
                if log.get('amount'):
                    file.write('\t\t<funds>' + str(log['amount']) + '</funds>\n')
            elif logType == 'quoteServer':
                file.write('\t\t<quoteServerTime>' + str(log['quoteServerTime']) + '</quoteServerTime>\n')
                file.write('\t\t<stockSymbol>' + str(log['stockSymbol']) + '</stockSymbol>\n')
                file.write('\t\t<price>' + str(log['price']) + '</price>\n')
                file.write('\t\t<cryptokey>' + str(log['cryptoKey']) + '</cryptokey>\n')
            elif logType == 'accountTransaction':
                file.write('\t\t<action>' + str(log['action']) + '</action>')
                file.write('\t\t<funds>' + str(log['amount']) + '</funds>')
            elif logType == 'systemEvent':
                file.write('\t\t<command>' + str(log['commandName']) + '</command>\n')
                if log.get('stockSymbol'):
                    file.write('\t\t<stockSymbol>' + str(log['stockSymbol']) + '</stockSymbol>\n')
                if log.get('fileName'):
                    file.write('\t\t<filename>' + str(log['fileName']) + '</filename>\n')
                if log.get('amount'):
                    file.write('\t\t<funds>' + str(log['amount']) + '</funds>\n')
            elif logType == 'errorMessage':
                file.write('\t\t<errorMessage>' + str(log['errorMessage']) + '</errorMessage>\n')
            elif logType == 'debugMessage':
                file.write('\t\t<debugMessage>' + str(log['debugMessage']) + '</debugMessage>\n')
            file.write('\t</'+ logType +'>\n')
        file.write('\n</log>\n')
        file.close()
        print "Log file written."

# Here we want our trigger's threads
# hitting the quote server for quotes every 15sec
# TODO: triggers cant actually just be used as client, because they have stuff reserved for them.
class hammerQuoteServerToBuy(Thread):
    def __init__(self, quoteServer):
        Thread.__init__(self)
        self.buyLock = threading.Lock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.daemon = True
        self.quote = quoteServer
        self.start()

    def run(self):
        while True:
            if not self.buyLock.locked():
                continue
            for symbol in localTriggers.buyTriggers:
                if len(localTriggers.buyTriggers[symbol]):
                    # get the id of someone for the request to the quote server
                    someonesUserId = localTriggers.buyTriggers[symbol].itervalues().next()
                    # TODO: should it be saved to the cache everytime we go straight to quote server?
                    transId = localTriggers.buyTriggers[symbol][someonesUserId]["transId"]
                    quote = self.quote.getQuote(symbol, someonesUserId, transId)
                    quoteValue = quote["value"]
                    for userId in localTriggers.buyTriggers[symbol]:
                        trigger = localTriggers.buyTriggers[symbol][userId]
                        if trigger["active"]:
                            if quoteValue <= trigger["buyAt"]:
                                args = {"sym": symbol, "userId": userId, "cash": trigger["maxSellAmount"]}
                                handleCommandBuy(args)
                                handleCommandCommitBuy(args)

            time.sleep(1)


class hammerQuoteServerToSell(Thread):
    def __init__(self, quoteServer):
        Thread.__init__(self)
        self.sellLock = threading.Lock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.daemon = True
        self.quote = quoteServer
        self.start()

    def run(self):
        while True:
            if not self.sellLock.locked():
                continue
            for symbol in localTriggers.buyTriggers:
                if len(localTriggers.buyTriggers[symbol]):
                    # get the id of someone for the request to the quote server
                    someonesUserId = localTriggers.sellTriggers[symbol].itervalues().next()
                    # TODO: should it be saved to the cache everytime we go straight to quote server?
                    transId = localTriggers.sellTriggers[symbol][someonesUserId]["transId"]
                    quote = self.quote.getQuote(symbol, someonesUserId, transId)
                    quoteValue = quote["value"]
                    for userId in localTriggers.sellTriggers[symbol]:
                        trigger = localTriggers.sellTriggers[symbol][userId]
                        if trigger["active"]:
                            if quoteValue >= trigger["sellAt"]:
                                args = {"sym": symbol, "userId": userId, "cash": trigger["maxSellAmount"]}
                                handleCommandSell(args)
                                handleCommandCommitSell(args)

            time.sleep(1)


# {
#     symbol : {
#        user1 :{
#            "cashReserved": cashReserved, "active": False, "buyAt": 0
#        }
#    }
# }

class Triggers:
    def __init__(self):
        self.buyTriggers = {}
        self.sellTriggers = {}

    def getBuyTriggers(self):
        return self.buyTriggers

    def getBuyTrigger(self, userId, symbol):
        if self._triggerExists(userId, symbol, self.buyTriggers):
            return self.buyTriggers[symbol][userId]
        return 0

    def getSellTriggers(self):
        return self.sellTriggers

    def getSellTrigger(self, userId, symbol):
        if self._triggerExists(userId, symbol, self.sellTriggers):
            return self.sellTriggers[symbol][userId]
        return 0

    def addBuyTrigger(self, userId, sym, cashReserved, transactionNumber):
        if userId not in self.buyTriggers:
            self.buyTriggers[userId] = {}
        self.buyTriggers[userId][sym] = {"cashReserved": cashReserved, "active": False, "buyAt": 0, "transId": transactionNumber}

    def addSellTrigger(self, userId, sym, maxSellAmount, transactionNumber):
        if userId not in self.sellTriggers:
            self.sellTriggers[userId] = {}
        self.sellTriggers[userId][sym] = {"maxSellAmount": maxSellAmount, "active": False, "sellAt": 0, "transId": transactionNumber}

    def setBuyActive(self, userId, symbol, buyAt):
        if self._triggerExists(userId, symbol, self.buyTriggers):
            print "activating buy thread"

            trigger = self.buyTriggers.get(symbol).get(userId)
            if buyAt <= trigger.get('cashReserved'):
                trigger["active"] = True
                trigger["buyAt"] = buyAt
                return trigger
        return 0

    def setSellActive(self, userId, symbol, sellAt):
        if self._triggerExists(userId, symbol, self.sellTriggers):
            trigger = self.sellTriggers.get(symbol).get(userId)
            if sellAt <= trigger.get('cashReserved'):
                trigger["active"] = True
                trigger["sellAt"] = sellAt
                return trigger
        return 0

    def cancelBuyTrigger(self, userId, symbol):
        # danger here'
        if self._triggerExists(userId, symbol, self.buyTriggers):
            hammerQuoteServerToBuy.buyLock.acquire()
            removedTrigger = self.buyTriggers[symbol][userId]
            del self.buyTriggers[symbol][userId]
            hammerQuoteServerToBuy.buyLock.realease()
            return removedTrigger
        return 0

    def cancelSellTrigger(self, userId, symbol):
        # danger here
        if self._triggerExists(userId, symbol, self.sellTriggers):
            hammerQuoteServerToSell.sellLock.acquire()
            removedTrigger = self.sellTriggers[symbol][userId]
            del self.sellTriggers[symbol][userId]
            hammerQuoteServerToSell.sellLock.realease()
            return removedTrigger
        return 0

    def _triggerExists(self, userId, symbol, triggers):
        if triggers.get(symbol):
            if triggers.get(symbol).get(userId):
                return 1
        return 0


# Class for users and database
# Users are stored:
#   {
#       userId: 'abc123',
#       cash: 0,
#       reserve: 0,
#       pendingBuys: [{symbol, number, timestamp}],
#       pendingSells: [{symbol, number, timestamp}],
#       portfolio: {symbol: {amount, reserved}}
#   }
# TODO: change strings to defined constants
'''
    TODO: consider throwing error instead of returning 0.
    some functions return numbers, and 0 would be a valid number to return
    like removing from portfolio

    OR

    change return of all functions to be the new user object, and 0 for failure
'''


class databaseServer:
    def __init__(self, transactionExpire=60):
        self.database = {}
        self.transactionExpire = transactionExpire  # for testing

    # returns user object for success
    # returns None for user not existing
    def getUser(self, userId):
        return self.database.get(userId)

    # returns user object for success
    # returns None for failure
    def addUser(self, userId):
        if userId not in self.database:
            user = {'userId': userId, 'cash': 0, 'reserve': 0, 'pendingBuys': [], 'pendingSells': [], 'portfolio': {}}
            self.database[userId] = user
            # not good but will work for now
            # adding user to threadhandler

            # ---for milestone1---
            # future add to a list of userID in threadhandler
            # start threads
            # threadBuyHandler.startBuyThread(userId)
            # threadSellHandler.startSellThread(userId)


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
    def pushBuy(self, userId, symbol, amount):
        user = self.getUser(userId)
        if not user:
            return 0
        newBuy = {'symbol': symbol, 'amount': amount, 'timestamp': int(time.time())}
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
    def pushSell(self, userId, symbol, amount):
        user = self.getUser(userId)
        if not user:
            return 0
        if not user['portfolio'].get(symbol):
            return 0
        newSell = {'symbol': symbol, 'amount': amount, 'timestamp': int(time.time())}
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

'''
    new stuff here, eventually, class quote should be gone, but in the sense of not breaking abunch of other stuff, its still there
'''
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
        print "sending Trigger request Id:", self.corr_id
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

    def getQuote(self, symbol, user, transactionNumber):
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
        return self._hitQuoteServerAndCache(symbol, user, transactionNumber)

    '''
        this can be used on buy commands
        that way we can guarantee the 60 seconds for a commit
        if we use cache, the quote could be 119 seconds old when they commit, and that breaks the requirements
    '''

    def getQuoteNoCache(self, symbol, user, transactionNumber):
        return self._hitQuoteServerAndCache(symbol, user, transactionNumber)

    def _hitQuoteServerAndCache(self, symbol, user, transactionNumber):
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
        #     transactionNumber,
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
            # TODO: not sure how filename comes in
            # USER_COMMAND
            # Create Requestbody to send to Audit Server
            # # requestBody= {("timeStamp": int(time.time() * 1000),
            #              "server":"transactionServer","transactionNum":args.get('lineNum'),"userId":args.get('userId'),
            #              "command":args.get("command"), "stockSymbol": args.get("stockSymbol"),
            #              "fileName":None,"amount":args.get("amount")
            #              }
            requestBody = auditFunctions.createUserCommand(int(time.time() * 1000,"transactionServer", args["lineNum"],
                                                args["userId"], args["command"],args.get("stockSymbol"),None,args.get("cash")))
            # Log User Command Call
            audit_rpc.call(requestBody)
            # # auditServer.logUserCommand(
            # #     int(time.time() * 1000),
            # #     "transaction",
            # #     args.get('lineNum'),
            # #     args.get('userId'),
            # #     args.get('command'),
            # #     stockSymbol=args.get('stockSymbol'),
            # #     fileName=None,
            # #     amount=args.get('cash')
            # # )
            # localDB.addUser(args["userId"])
        else:
            # TODO: not sure how filename comes in
            requestBody = auditFunctions.createUserCommand(int(time.time() * 1000, "transactionServer", args["lineNum"],
                                                               args["userId"], args["command"], args.get("stockSymbol"),
                                                               args["userId"], args.get("cash")))
            # Log User Command Call
            audit_rpc.call(requestBody)
            # Log DumpLog Call
            # requestBody = {"function": "WRITE_LOGS","fileName": args.get("userId")}
            # audit_rpc.call(requestBody)

            # auditServer.writeLogs(fileName)



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

        # triggers
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
        else:
            print "couldn't figure out command..."
    except RuntimeError:
        # (self, timeStamp, server, transactionNum, userId, commandName, errorMessage)
        # errror msg being sent to audit server
        requestBody = {"function": "ERROR_MESSAGE", "timeStamp": int(time.time() * 1000),
                       "server": "transactionServer", "transactionNum": args.get('lineNum'),
                       "userId": args.get('userId'),"command": args.get("command"), "errorMessage": RuntimeError
                       }
        requestBody = auditFunctions.createErrorMessage(int(time.time() * 1000, "transactionServer", args["lineNum"],
                                                               args["userId"], args["command"],str(RuntimeError)))
        audit_rpc.call(requestBody)
    except TypeError:
        # errror msg being sent to audit server
        requestBody = auditFunctions.createErrorMessage(int(time.time() * 1000, "transactionServer", args["lineNum"],
                                                            args["userId"], args["command"], str(RuntimeError)))
        audit_rpc.call(requestBody)
    except ArithmeticError:
        # errror msg being sent to audit server
        requestBody = auditFunctions.createErrorMessage(int(time.time() * 1000, "transactionServer", args["lineNum"],
                                                            args["userId"], args["command"], str(RuntimeError)))
        audit_rpc.call(requestBody)

def handleCommandQuote(args):
    symbol = args["stockSymbol"]
    userId = args["userId"]
    transactionNumber = args["lineNum"]

    request = createQuoteRequest(userId, symbol, transactionNumber)
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
    transactionNumber = args["lineNum"]

    popRequest = databaseFunctions.createPopBuyRequest(userId)
    popResponse = db_rpc.call(popRequest)
    if popResponse["status"] == 200:
        buy = popResponse["body"]
        quote = createQuoteRequest(userId, buy["symbol"], transactionNumber)
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
    transactionNumber = args["lineNum"]

    popRequest = databaseFunctions.createPopSellRequest(userId)
    popResponse = db_rpc.call(popRequest)
    if popResponse["status"] == 200:
        sell = popResponse["body"]
        quote = createQuoteRequest(userId, sell["symbol"], transactionNumber)
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
    transactionNumber = args.get("lineNum")

    reserveRequest = databaseFunctions.createReserveCashRequest(userId, amount)
    reserveResponse = db_rpc.call(reserveRequest)
    if reserveResponse["status"] == 200:
        buyRequest = TriggerFunctions.createAddBuyRequest(userId, symbol, amount, transactionNumber)
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
    transactionNumber = args.get("lineNum")

    sellRequest = TriggerFunctions.createAddSellRequest(userId, symbol, amount, transactionNumber)
    sellResponse = trigger_rpc.call(sellRequest)


def handleCommandSetSellTrigger(args):
    symbol = args.get("stockSymbol")
    sellAt = args.get("cash")
    userId = args.get("userId")

    getTriggerRequest = TriggerFunctions.createGetSellRequest(userId, symbol)
    getTriggerResponse = trigger_rpc.call(getTriggerRequest)
    if getTriggerResponse["status"] == 200:
        trigger = getTriggerRequest["body"]
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
    # Global vars
    # -----------------------
    # auditServer = AuditServer()
    # quoteObj = Quotes(auditServer)
    localDB = databaseServer()
    localTriggers = Triggers()

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
