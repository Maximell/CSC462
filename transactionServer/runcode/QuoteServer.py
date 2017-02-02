import socket
import time
from random import randint

from OpenSSL import SSL


# quote shape: symbol: {value: string, retrieved: epoch time, user: string, cryptoKey: string}
class Quotes():
    def __init__(self, auditServer, cacheExpire=60, testing=False):
        self.cacheExpire = cacheExpire
        self.quoteCache = {}
        self.testing = testing
        self.auditServer = auditServer
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

        self.auditServer.logQuoteServer(
            int(time.time() * 1000),
            "quote",
            transactionNumber,
            user,
            newQuote.get('serverTime'),
            symbol,
            newQuote.get('value'),
            newQuote.get('cryptoKey')
        )

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