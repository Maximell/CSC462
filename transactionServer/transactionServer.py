
# demonstrate talking to the quote server
import socket, sys
from OpenSSL import SSL
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from SocketServer import BaseServer
import os
import json
import pprint
import time
from random import randint


# COMMANDS NEEDED
#
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
#
# dumplog    (x2)
# display_summary
#

# Dictionary for users and database
# Users are stored:
#   {
#       userId: 'abc123',
#       cash: 0,
#       reserve: 0,
#         pendingBuys: [{symbol, number, timestamp}],
#         pendingSells: [{symbol, number, timestamp}],
#         portfolio: {}
#   }
class databaseServer:

    def __init__(self, transactionExpire=60):
        self.database = {}
        self.transactionExpire = transactionExpire

    # returns user object for success
    # returns None for user not existing
    def getUser(self, userId):
        return self.database.get(userId)

    # returns user object for success
    # returns None for failure
    def addUser(self, userId):
        user = { 'userId': userId, 'cash': 0, 'reserve': 0, 'pendingBuys': [], 'pendingSells': [], 'portfolio': {}}
        self.database[userId] = user
        return self.database.get(userId)

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
            user['cash'] = user.get('cash') + amount
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

    #TODO: test in databaseServerTester.py
    def pushBuy(self, userId, symbol, number):
        user = self.database.get(userId)
        if not user:
            return 0
        # {symbol, number, timestamp}
        newBuy = {'symbol': symbol, 'number': number, 'timestamp': int(time.time())}
        user.get('pendingBuys').append(newBuy)
        return newBuy

    # TODO: test in databaseServerTester.py
    def popBuy(self, userId):
        user = self.database.get(userId)
        if not user:
            return 0
        pendingBuys = user.get('pendingBuys')
        if not len(pendingBuys):
            return 0
        return pendingBuys.pop()

    # TODO: test in databaseServerTester.py
    def pushSell(self, userId, symbol, number):
        user = self.database.get(userId)
        if not user:
            return 0
        # {symbol, number, timestamp}
        newSell = {'symbol': symbol, 'number': number, 'timestamp': int(time.time())}
        user.get('pendingSells').append(newSell)
        return newSell

    # TODO: test in databaseServerTester.py
    def popSell(self, userId):
        user = self.database.get(userId)
        if not user:
            return 0
        pendingSells = user.get('pendingSells')
        if not len(pendingSells):
            return 0
        return pendingSells.pop()

    # TODO: test in databaseServerTester.py
    def isBuySellActive(self, buyOrSell):
        return (int(buyOrSell.get('timestamp', 0)) + self.transactionExpire) > int(time.time())



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
            if self._cacheIsActive(cache):
                self._testPrint(False, "from cache")
                return cache
            self._testPrint(False, "expired cache")

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
            s.connect(('quoteserve.seng.uvic.ca', 4442))

            socket.send(request)
            data = socket.recv(1024)

            s.close()

        newQuote = self._quoteStringToDictionary(data)
        self.quoteCache[symbol] = newQuote
        return newQuote

    def _quoteStringToDictionary(self, quoteString):
        # "quote, sym, userid, timestamp, cryptokey\n"
        split = quoteString.split(",")
        return {'value': split[0], 'retrieved': split[3], 'user': split[2]}

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
                # print self.command
                # print self.request
                self.send_response(200)
                self.handle()
            else:
                self.send_response(400)
        except:
            self.handle_error()

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print("%s wrote:" % self.client_address[0])

        # just send back the same data, but upper-cased
        self.request.send(self.data.upper())
        extractData(self.data)

def extractData(data):
    # extracting data and splitting properly
    list = data.split('\n')
    for x in range(0,len(list)):
        list[x] = list[x].strip('\r')
    # request is the actual args we need
    # lineNum , userID , CMD
    # ------------------------------------
    # NOTE: not sure where the sym is???
    # ------------------------------------

    request = list[-1]
    requestlist = request.split('&')

    for x in range(0,len(requestlist)):
        requestlist[x] = requestlist[x].split('=')
    print requestlist
    deligate(requestlist)

def deligate(args):
    # this is where we will figure what CMD we are dealing with
    # and deligate from here to whatever function is needed
    # to handle the request
    pass



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

def checkUser(userID):
    # adding user to DB
    # NOTE (usersnames need newline char to activate quoteserver)
    if userID not in dict:
        dict[userID] = 0
        print "adding user"



if __name__ == '__main__':
    main()