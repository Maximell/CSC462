#!/usr/bin/env python
import socket
import time
import json
from random import randint
import pika
from rabbitMQSetups import RabbitMQClient, RabbitMQReceiver
from mqAuditServer import auditFunctions



def createQuoteRequest(userId, stockSymbol, lineNum, args):
    args.update({"userId": userId, "stockSymbol": stockSymbol, "lineNum": lineNum})
    return args

# quote shape: symbol: {value: string, retrieved: epoch time, user: string, cryptoKey: string}
class Quotes():
    def __init__(self, cacheExpire=60, testing=False):
        self.cacheExpire = cacheExpire
        self.quoteCache = {}
        self.testing = testing
        self.count = 0

    def getQuote(self, symbol, user, transactionNum):
        self._testPrint(True, "current cache state: ", self.quoteCache)

        cache = self.quoteCache.get(symbol)
        if cache:
            if self._cacheIsActive(cache):
                self._testPrint(False, "from cache")
                return cache
            self._testPrint(False, "expired cache")
        return self._hitQuoteServerAndCache(symbol, user, transactionNum)

    def _hitQuoteServerAndCache(self, symbol, user, transactionNum):
        self._testPrint(False, "not from cache")
        request = symbol + "," + user + "\n"

        if self.testing:
            data = self._mockQuoteServer(request)
            newQuote = self._quoteStringToDictionary(data)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('quoteserve.seng.uvic.ca', 4445))
            s.send(request)
            data = s.recv(1024)
            s.close()
            newQuote = self._quoteStringToDictionary(data)
            requestBody = auditFunctions.createQuoteServer(
                int(time.time() * 1000),
                "quoteServer",
                transactionNum,
                user,
                newQuote['serverTime'],
                symbol,
                newQuote['value'],
                newQuote['cryptoKey']
            )
            auditClient.send(requestBody)

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
        quoteArray = [randint(0, 50), symbol, user, int(time.time()), "cryptokey" + repr(randint(0, 50))]
        return ','.join(map(str, quoteArray))

    def _testPrint(self, newLine, *args):
        if self.testing:
            for arg in args:
                print arg,
            if newLine:
                print

    def _printQuoteCacheState(self):
        print self.quoteCache



def on_request(ch, method, props, body):
    # expected body: {symbol, userId, transactionNum}
    payload = json.loads(body)
    print "received payload", payload

    symbol = payload["stockSymbol"]
    userId = payload["userId"]
    lineNum = payload["lineNum"]

    quote = quoteServer.getQuote(symbol, userId, lineNum)
    print "quote: ", quote

    payload["quote"] = quote["value"]
    payload["cryptoKey"] = quote["cryptoKey"]
    payload["quoteRetrieved"] = quote["retrieved"]

    print "sending back:", payload
    transactionServerID = payload["trans"]
    # Need to figure out which transaction server to send back to.
    transactionClient = RabbitMQClient(transactionServerID)
    if quoteServer.count % 50 == 0:
        transactionClient.send(payload , processEvents=True)
    else:
        transactionClient.send(payload)
    quoteServer.count += 1

if __name__ == '__main__':
    print "starting QuoteServer"
    quoteServer = Quotes()

    auditClient = RabbitMQClient(RabbitMQClient.AUDIT)
    # transactionClient = RabbitMQClient(RabbitMQClient.TRANSACTION)
    print "Awaiting quote requests"
    RabbitMQReceiver(on_request, RabbitMQReceiver.QUOTE)

