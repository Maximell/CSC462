#!/usr/bin/env python
import pika
import socket
import time
import json
import uuid
from random import randint
from rabbitMQSetups import RabbitMQClient, RabbitMQReceiver
from mqAuditServer import auditFunctions


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
        print "sending quote request Id:", self.corr_id
        requestBody = json.dumps(requestBody)
        # print type(requestBody)
        self.channel.basic_publish(
            exchange='',
            routing_key=RabbitMQClient.AUDIT,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body=requestBody
        )
        while self.response is None:
            self.connection.process_data_events()

        print "From Audit Server: ", self.response
        return self.response

def createQuoteRequest(userId, symbol, transactionNum):
    return {"userId": userId, "stockSymbol": symbol, "lineNum": transactionNum}

# quote shape: symbol: {value: string, retrieved: epoch time, user: string, cryptoKey: string}
class Quotes():
    def __init__(self, cacheExpire=60, testing=False):
        self.cacheExpire = cacheExpire
        self.quoteCache = {}
        self.testing = testing

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
            requestBody = auditFunctions.createQuoteServer(int(time.time() * 1000),"quoteServer", transactionNum,user, newQuote['serverTime'],
                                             symbol,newQuote['value'],newQuote['cryptoKey'] )
            print requestBody
            print type(requestBody)
            audit_rpc.call(requestBody)


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
    payload = json.loads(body)
    print payload
    # expected body: {symbol, userId, transactionNum}
    # payload = json.loads(body)
    symbol = payload["stockSymbol"]
    userId = payload["userId"]
    lineNum = payload["lineNum"]

    quote = quoteServer.getQuote(symbol, userId, lineNum)

    payload["quote"] = quote["value"]
    payload["cryptoKey"] = quote["cryptoKey"]

    transactionClient.send(payload)


if __name__ == '__main__':
    print "starting QuoteServer"
    quoteServer = Quotes()
    audit_rpc = AuditRpcClient()
    transactionClient = RabbitMQClient(RabbitMQClient.TRANSACTION)

    RabbitMQReceiver(on_request, RabbitMQReceiver.QUOTE)

