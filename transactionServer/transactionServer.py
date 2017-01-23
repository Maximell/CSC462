
# demonstrate talking to the quote server
import socket
import time
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import BaseServer
from random import randint
import math
# import urllib
import urlparse
from OpenSSL import SSL
import sched, time
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
class loggerServer:

    def __init__(self):
        self.logFile = []

    def log(action):
        print 'Logging an action: ' + action + '.'
# '''
#     def logUserCommand():
#     def logQuoteServerHit():
#     def logAccountChange():
#     def logSystemEvent():
#     def logErrorMessage():
#     def logDebugMessage(server, timestamp, transactionNum, command, userId, stockSymbol, fileName, funds, debugMessage):
# '''
    def writeLogs(fileName):
        print 'trying to print contents to file: %s.' % (fileName)

    # writes a single line to the log file
    def _writeLineToLogFile(self,line):
        self.logFile.append(line)
        return

    # writes a list of lines to the log file
    def _writeLinesToLogFile(self,lines):
        self.logFile.extend(lines)
        return

    # dumps the logs to a given file
    def _dumpIntoFile(self,fileName):
        try:
            file = open(fileName, 'w')
        except IOError:
            print 'Attempted to save into file %s but couldn\'t open file for writing.' % (fileName)
        for line in self.logFile:
            file.write(line)
        file.close()


# Class for users and database
# Users are stored:
#   {
#       userId: 'abc123',
#       cash: 0,
#       reserve: 0,
#         pendingBuys: [{symbol, number, timestamp}],
#         pendingSells: [{symbol, number, timestamp}],
#         portfolio: {symbol: amount, symbol2: amount}
#   }
# TODO: change strings to defined constants
'''
    TODO: consider throwing error instead of returning 0.
    some functions return numbers, and 0 would be a valid number to return
    like removing from portfolio

    OR

    change return of all functions to be the new user object, and 0 for failure
'''


# class trigger:
#     def __init__(self, userID, sym, price, ):
#         self.userID = userID
#         self.sym = sym
#         self.price = price
#         self.active = False
#     def activate(self):
#         self.active = True

class triggerHandler:
    def __init__(self):
        self.buyTriggers = {}
        self.sellTriggers = {}

    def addBuyTrigger(self, userId, sym, reserved):
        if userId not in self.buyTriggers:
            self.buyTriggers[userId] = {}
        self.buyTriggers[userId][sym] = {"reserved": reserved, "active": False, "buyAt": 0}

    def addSellTrigger(self, userId, sym, reserved):
        if userId not in self.sellTriggers:
            self.sellTriggers[userId] = {}
        self.sellTriggers[userId][sym] = {"reserved": reserved, "active": False, "buyAt": 0}

    def setBuyActive(self, userId, sym, buyAt):
        if self.buyTriggers.get(userId):
            if self.buyTriggers.get(userId).get(sym):
                self.buyTriggers.get(userId).get(sym)["active"] = True
                self.buyTriggers.get(userId).get(sym)["buyAt"] = buyAt
                return self.buyTriggers.get(userId).get(sym)
        return 0

    def setSellActive(self , userId , sym, buyAt):
        if self.sellTriggers.get(userId):
            if self.sellTriggers.get(userId).get(sym):
                self.sellTriggers.get(userId).get(sym)["active"] = True
                self.sellTriggers.get(userId).get(sym)["buyAt"] = buyAt
                return self.sellTriggers.get(userId).get(sym)
        return 0

    def cancelBuyTrigger(self, userId, symbol):
        if self.buyTriggers.get(userId):
            if self.buyTriggers.get(userId).get(symbol):
                del self.buyTriggers[userId][symbol]
                return 1
        return 0

    def cancelSellTrigger(self, userId, symbol):
        if self.sellTriggers.get(userId):
            if self.sellTriggers.get(userId).get(symbol):
                del self.sellTriggers[userId][symbol]
                return 1
        return 0


class databaseServer:

    def __init__(self, transactionExpire=60):
        self.database = {}
        self.transactionExpire = transactionExpire # for testing

    # returns user object for success
    # returns None for user not existing
    def getUser(self, userId):
        return self.database.get(userId)

    # returns user object for success
    # returns None for failure
    def addUser(self, userId):
        if userId not in self.database:
            user = { 'userId': userId, 'cash': 0, 'reserve': 0, 'pendingBuys': [], 'pendingSells': [], 'portfolio': {}}
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
            user = { 'userId': userId, 'cash': amount, 'reserve': 0 }
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
        portfolioAmount = user.get('portfolio').get(symbol)
        # cant sell portfolio that doesnt exist
        if portfolioAmount is None:
            return False
        # trying to sell more than they own
        if portfolioAmount < amount:
            return False

        user['portfolio'][symbol] -= amount
        return user['portfolio'][symbol]

    # returns new amount
    # returns False for error
    def addToPortfolio(self, userId, symbol, amount):
        user = self.getUser(userId)
        if not user:
            return False
        portfolioAmount = user.get('portfolio').get(symbol)
        if portfolioAmount is None:
            user['portfolio'][symbol] = 0

        user['portfolio'][symbol] = amount
        return user['portfolio'][symbol]

    def checkPortfolio(self, userId):
        user = self.getUser(userId)
        return user.get('portfolio')



# quote shape: symbol: {value: string, retrieved: epoch time, user: string}
class Quotes():
    def __init__(self, cacheExpire=60, testing=False):
        self.cacheExpire = cacheExpire
        self.quoteCache = {}
        self.testing = testing

    def getQuote(self, symbol, user):
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
        return self._hitQuoteServerAndCache(symbol, user)

    '''
        this can be used on buy commands
        that way we can guarantee the 60 seconds for a commit
        if we use cache, the quote could be 119 seconds old when they commit, and that breaks the requirements
    '''
    def getQuoteNoCache(self, symbol, user):
        return self._hitQuoteServerAndCache(symbol, user)

    def _hitQuoteServerAndCache(self, symbol, user):
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

        newQuote = self._quoteStringToDictionary(data)
        self.quoteCache[symbol] = newQuote
        return newQuote

    def _quoteStringToDictionary(self, quoteString):
        # "quote, sym, userid, timestamp, cryptokey\n"
        split = quoteString.split(",")
        return {'value': float(split[0]), 'retrieved': split[3], 'user': split[2]}

    def _cacheIsActive(self, quote):
        return (int(quote.get('retrieved', 0)) + self.cacheExpire) > int(time.time())

    def _mockQuoteServer(self, queryString):
        query = queryString.split(",")
        symbol = query[0]
        user = query[1]
        quoteArray = [randint(0,50), symbol, user, int(time.time()), "cryptokey"]
        return ','.join(map(str, quoteArray))

    def _testPrint(self, newLine, *args):
        if self.testing:
            for arg in args:
                print arg,
            if newLine:
                print

    def _printQuoteCacheState(self):
        print self.quoteCache

class httpsServer(HTTPServer):
    def __init__(self, serverAddr, handlerClass ):
        BaseServer.__init__(self, serverAddr, handlerClass)
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        # server.pem's location (containing the server private key and
        # the server certificate).
        fpem = "cert.pem"
        ctx.use_privatekey_file(fpem)
        ctx.use_certificate_file(fpem)
        self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
                                                        self.socket_type))
        self.server_bind()
        self.server_activate()

    def shutdown_request(self, request):
        request.shutdown()
    # def parse_request(self , request):
    #     print "servicing"

class httpsRequestHandler(SimpleHTTPRequestHandler):
    def setup(self):
        self.connection = self.request
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)
        self.rfile = socket._fileobject(self.request, "rb", self.wbufsize)

    def do_GET(self):
        print self.command
        self.send_response(200)

    def do_POST(self):
        try:
            if self.request != None:
                self.handle()
                self.send_response(200)

            else:
                self.send_response(400)
        except:
            self.handle_error()

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        # just send back the same data, but upper-cased
        self.request.send(self.data.upper())
        extractData(self.data)





def extractData(data):
    # extracting data and splitting properly

    args = urlparse.parse_qs(data)
    # print args
    splitInfo = args["args"][0].split()
    sanitized = []
    # removing chars to make args easier to deal with
    # in the future
    for x in splitInfo:
        x = x.strip('[')
        x = x.strip(']')
        x = x.strip('\'')
        x = x.strip(',')
        x = x.strip('\'')
        sanitized.append(x)

    args["userId"] = sanitized[0]
    args["command"] = args["command"][0]
    # extracting the line number
    for key, value in args.iteritems():
        string = str(key[0]) + str(key[1]) + str(key[2]) + str(key[3])
        if string == "POST":
            args["lineNum"] = value[0]
            del args[key]
            break

    #   depending on what command we have
    if len(sanitized) == 2:
        # 2 case: 1 where userId and sym
        #         2 where userId and cash
        if args["command"] == 'ADD':
            args["cash"] = sanitized[1]
        else:
            args["sym"] = sanitized[1]
    if len(sanitized) == 3:
        args["sym"] = sanitized[1]
        args["cash"] = float(sanitized[2])

    del args["args"]
    # args now has keys: userId , sym , lineNUM , command , cash
    #
    # {'userId': 'oY01WVirLr', 'cash': '63511.53',
    # 'lineNum': '1', 'command': 'ADD'}
    
    '''
        This should be changed to use the Events class - when it is done.
    '''

    delegate(args)

def delegate(args):
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

    # Call Quote
    localDB.addUser(args["userId"])
    if args["command"] == "QUOTE":
        print "getting Quote"
        quoteObj.getQuote( args["sym"] , args["userId"])
        quoteObj._printQuoteCacheState()
        pass
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
        pass
    elif args["command"] == "CANCEL_BUY_AMOUNT":
        pass
    elif args["command"] == "SET_BUY_TRIGGER":

        pass

    elif args["command"] == "SET_SELL_AMOUNT":
        pass
    elif args["command"] == "CANCEL_SELL_AMOUNT":
        pass
    elif args["command"] == "SET_SELL_TRIGGER":
        pass



def handleCommandAdd(args):
    localDB.addCash(args["userId"], args["cash"])

def handleCommandBuy(args):
    symbol = args.get("sym")
    cash = args.get("cash")
    userId = args.get("userId")

    if localDB.getUser(userId).get("cash") >= cash:
        quote = quoteObj.getQuoteNoCache(symbol, args["userId"])

        costPer = quote.get('value')
        amount = int(cash / costPer)

        localDB.pushBuy(userId, symbol, amount, costPer)
        localDB.reserveCash(userId, amount * costPer)
    else:
        return "not enough available cash"

def handleCommandCommitBuy(args):
    userId = args.get("userId")
    buy = localDB.popBuy(userId)
    if buy:
        symbol = buy.get('symbol')
        number = buy.get('number')
        costPer = buy.get('costPer')
        if localDB.isBuySellActive(buy):
            localDB.addToPortfolio(userId, symbol, number)
            localDB.commitReserveCash(userId, number * costPer)
        else:
            localDB.releaseCash(userId, number * costPer)
            return "inactive"
    else:
        return "no buys"

def handleCommandCancelBuy(args):
    userId = args.get("userId")
    buy = localDB.popBuy(userId)
    if buy:
        number = buy.get('number')
        costPer = buy.get('costPer')
        localDB.releaseCash(userId, number * costPer)
    else:
        return "no buys"

def handleCommandSell(args):
    symbol = args.get("sym")
    cash = args.get("cash")
    userId = args.get("userId")

    quote = quoteObj.getQuoteNoCache(symbol, args["userId"])

    costPer = quote.get('value')
    amount = math.floor(cash / costPer)


    localDB.pushSell(userId, symbol, amount, costPer)

def handleCommandCommitSell(args):
    userId = args.get("userId")
    sell = localDB.popSell(userId)
    if sell:
        symbol = sell.get('symbol')
        number = sell.get('number')
        costPer = sell.get('costPer')
        if localDB.isBuySellActive(sell):
            localDB.removeFromPortfolio(userId, symbol, number)
            localDB.addCash(userId, number * costPer)
        else:
            return "inactive"
    else:
        return "no sells"

def handleCommandCancelSell(args):
    userId = args.get("userId")
    sell = localDB.popSell(userId)
    if not sell:
        return "no sells"


def main():
#   starting httpserver and waiting for input
    spoolUpServer()


def spoolUpServer(handlerClass = httpsRequestHandler, serverClass = httpsServer):
    socknum = 4442

    try:
        serverAddr = ('', socknum)  # our address and port
        httpd = serverClass(serverAddr, handlerClass)
    except socket.error:
        print "socket:" + str(socknum) + " busy."
        socknum = incrementSocketNum(socknum)
        serverAddr = ('', socknum)  # our address and port
        httpd = serverClass(serverAddr, handlerClass)

    socketName = httpd.socket.getsockname()
    print "serving HTTPS on" , socketName[0], "port number:", socketName[1],
    print "waiting for request..."
    # this idles the server waiting for requests
    httpd.serve_forever()

def incrementSocketNum(socketNum):
    # This is used to increment the socket incase ours is being used
    socketNum += 1
    return socketNum

if __name__ == '__main__':
    # Global vars
    # -----------------------
    quoteObj = Quotes()
    localDB = databaseServer()
    localTriggers = triggerHandler()
    # -----------------------

    main()
    # send dumplog
    #