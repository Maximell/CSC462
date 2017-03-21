#!/usr/bin/env python
import socket
import time
import json
from random import randint
import pika
from threading import Thread
import threading
from rabbitMQSetups import RabbitMQClient, RabbitMQReceiver
from mqAuditServer import auditFunctions



def createQuoteRequest(userId, stockSymbol, lineNum, args):
    args.update({"userId": userId, "stockSymbol": stockSymbol, "lineNum": lineNum})
    return args

class poolHandler(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.curCacheSize = len(quoteServer.quoteCache)
        self.start()

    def run(self):
        print "starting thread for poolhandler"
        while(True):
#         look between pool of requests
#          and the cache size.
            if len(quoteServer.quoteCache) != self.curCacheSize:
                self.curCacheSize = len(quoteServer.quoteCache)
                for sym in quoteServer.pool:
                    quote = quoteServer.quoteCache.get(sym)
                    if quote is not None:
                        for payload in quoteServer.pool[sym]:
                            print "found a match for: ", sym
                            # if payload sym in cache
                            payload["quote"] = quote["value"]
                            payload["cryptoKey"] = quote["cryptoKey"]
                            payload["quoteRetrieved"] = quote["retrieved"]

                            print "sending back form handler:", payload
                            transactionServerID = payload["trans"]
                            # Need to figure out which transaction server to send back to.
                            transactionClient = RabbitMQClient(transactionServerID)
                            transactionClient.send(payload)
                        quoteServer.pool[sym] = []


class getQuoteThread(Thread):
    def __init__(self , symbol , user , transactionNum):
        Thread.__init__(self)
        self.cacheLock = threading.Lock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.daemon = True
        # package to go to quote server
        self.symbol = symbol
        self.userId = user
        self.transactionNum = transactionNum
        # self.portNum  = portNum
        self.start()

    def run(self):
        request = self.symbol + "," + self.userId + "\n"
        # print "request to quoteserver: ", request
        # print "portNum:", self.portNum
        self.socket.connect(('quoteserve.seng.uvic.ca', 4442 ))
        self.socket.send(request)
        data = self.socket.recv(1024)
        self.socket.close()
        # print "close socket"
        # reset port to 0
        # quoteServer.quotePorts[self.portNum] = 0
        # quoteServer.MaxThreads += 1
        # #
        # print "new quote to string"
        newQuote = quoteServer.quoteStringToDictionary(data)
        # newQuote = {"value": 10, "cryptoKey": 'abc', "retrieved": int(time.time())}
        print "got new quote from server: ",newQuote
        requestBody = auditFunctions.createQuoteServer(
            int(time.time() * 1000),
            "quoteServer",
            self.transactionNum,
            self.userId,
            newQuote['serverTime'],
            self.symbol,
            newQuote['value'],
            newQuote['cryptoKey']
        )
        print "built request: ",requestBody
        auditClient.send(requestBody)
        # print
        #     TODO might have to lock between all threads
        # if not self.cacheLock.locked():

        self.cacheLock.acquire()
        quoteServer.quoteCache[self.symbol] = newQuote
        del quoteServer.inflight[quoteServer.inflight.index(self.symbol)]
        self.cacheLock.release()



# quote shape: symbol: {value: string, retrieved: epoch time, user: string, cryptoKey: string}
class Quotes():
    def __init__(self, cacheExpire=60, ):
        self.cacheExpire = cacheExpire
        self.quoteCache = {}
        self.inflight = []
        # self.MaxThreads = 9
        # self.quotePorts = {4441:0,4443:0,4444:0,4445:0,4446:0,4447:0,4448:0,4449:0}
        self.pool = {}


    def getQuote(self, symbol , user , transactionNum):
        cache = self.quoteCache.get(symbol)
        print "checking quote cache: ", cache,  symbol
        print "current cache = ",self.quoteCache
        if cache:
            if self._cacheIsActive(cache):
                print "cache value is active"
                return cache
        self.hitQuoteServerAndCache(symbol, user, transactionNum)
        return

    def hitQuoteServerAndCache(self, symbol, user, transactionNum):
        # run new quote thread
        if symbol in self.inflight:
            return

        # while(self.MaxThreads == 0):
            # loop while all threads are taken
            # pass
        # print "free port"
        # for port in self.quotePorts:
        #     if self.quotePorts[port] == 0:
        #         print "new thread on port: ",port
        getQuoteThread(symbol , user , transactionNum)
        # self.quotePorts[port] = 1
        self.inflight.append(symbol)
        # self.MaxThreads -= 1
        # print "maxthreads = ",self.MaxThreads
        # added sym to quoteserver.inflight



    def quoteStringToDictionary(self, quoteString):
        # "quote, sym, userId, timeStamp, cryptokey\n"
        split = quoteString.split(",")
        return {'value': float(split[0]), 'retrieved': int(split[3])/1000, 'serverTime': split[3], 'cryptoKey': split[4].strip("\n")}

    def _cacheIsActive(self, quote):
        print "_cacheIsActive", (int(quote.get('retrieved', 0)) + self.cacheExpire),  int(time.time())
        print "returning", (int(quote.get('retrieved', 0)) + self.cacheExpire) > int(time.time())
        return (int(quote.get('retrieved', 0)) + self.cacheExpire) > int(time.time())

    def _mockQuoteServer(self, queryString):
        query = queryString.split(",")
        symbol = query[0]
        user = query[1]
        quoteArray = [randint(0, 50), symbol, user, int(time.time()), "cryptokey" + repr(randint(0, 50))]
        return ','.join(map(str, quoteArray))


    def _printQuoteCacheState(self):
        print self.quoteCache
    def addRequestToPool(self, payload):
        symbol = payload["stockSymbol"]
        if self.pool.get(symbol) is None:
            self.pool[symbol] = []
        self.pool[symbol].append(payload)




def on_request(ch, method, props, body):
    # expected body: {symbol, userId, transactionNum}
    payload = json.loads(body)
    print "received payload", payload

    symbol = payload["stockSymbol"]
    userId = payload["userId"]
    lineNum = payload["lineNum"]

    quote = quoteServer.getQuote(symbol, userId, lineNum)
    # quote = {"value": 10, "cryptoKey": 'abc', "retrieved": int(time.time())}
    print "return from quote cache: ", quote
#     go in pool
    if quote is None:
        print "going into pool"
        quoteServer.addRequestToPool(payload)
        return

    print "quote: ", quote

    payload["quote"] = quote["value"]
    payload["cryptoKey"] = quote["cryptoKey"]
    payload["quoteRetrieved"] = quote["retrieved"]

    print "sending back from cache:", payload
    transactionServerID = payload["trans"]
    # Need to figure out which transaction server to send back to.
    transactionClient = RabbitMQClient(transactionServerID)
    transactionClient.send(payload)

if __name__ == '__main__':
    print "starting QuoteServer"
    quoteServer = Quotes()
    poolHandler()

    auditClient = RabbitMQClient(RabbitMQClient.AUDIT)
    # transactionClient = RabbitMQClient(RabbitMQClient.TRANSACTION)
    print "Awaiting quote requests"
    RabbitMQReceiver(on_request, RabbitMQReceiver.QUOTE)

