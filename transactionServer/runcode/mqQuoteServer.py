#!/usr/bin/env python
import pika
import socket
import time
from random import randint
import json
import queueNames


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

def createQuoteRequest(userId, symbol, transactionNumber):
    return {"userId": userId, "symbol": symbol, "transactionNumber": transactionNumber}

# quote shape: symbol: {value: string, retrieved: epoch time, user: string, cryptoKey: string}
class Quotes():
    def __init__(self, cacheExpire=60, testing=False):
        self.cacheExpire = cacheExpire
        self.quoteCache = {}
        self.testing = testing

    def getQuote(self, symbol, user, transactionNumber):
        self._testPrint(True, "current cache state: ", self.quoteCache)

        cache = self.quoteCache.get(symbol)
        if cache:
            if self._cacheIsActive(cache):
                self._testPrint(False, "from cache")
                return cache
            self._testPrint(False, "expired cache")
        return self._hitQuoteServerAndCache(symbol, user, transactionNumber)


    def _hitQuoteServerAndCache(self, symbol, user, transactionNumber):
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
            audit_rpc.call(requestBody={"function": "QUOTE_SERVER","timeStamp":int(time.time()*1000),"server":"quoteServer",
                                        "transactionNum": transactionNumber, "userId":user ,"quoteServerTime":newQuote.get('serverTime'),
                                         "stockSymbol":symbol,"price":newQuote.get("value"),"cyptoKey":newQuote.get("cryptoKey")})
        #     Sent auditServer Quote Log

        # auditServer.logQuoteServer(payload.get("timeStamp"), payload.get("server"), payload.get("transactionNum"),
        #                            payload.get("userId"), payload.get("quoteServerTime"), payload.get("stockSymbol"),
        #                            payload.get("amount"), payload.get("cyptoKey"))
        # requestBody = {"function": "USER_COMMAND", "transactionNum": int(time.time() * 1000),
        #                "server": "transactionServer", "lineNum": args.get('lineNum'), "userId": args.get('userId'),
        #                "command": args.get("command"), "stockSymbol": args.get("stockSymbol"),
        #                "fileName": None, "amount": args.get("amount")
        #                }
        # TODO: send to audit server
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
    try:
        # expected body: {symbol, userId, transactionNumber}
        payload = json.loads(body)
        symbol = payload["symbol"]
        userId = payload["userId"]
        transactionNumber = payload["transactionNumber"]

        quote = quoteServer.getQuote(symbol, userId, transactionNumber)
        response = json.dumps(quote)
        print "got", response, "for", props.correlation_id

        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=response
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except RuntimeError:
        # (self, timeStamp, server, transactionNum, userId, commandName, errorMessage)
        # errror msg being sent to audit server
        requestBody = {"function": "ERROR_MESSAGE", "timeStamp": int(time.time() * 1000),
                       "server": "quoteServer", "transactionNum": payload.get('lineNum'),
                       "userId": payload.get('userId'),"command": payload.get("command"),
                       "errorMessage": RuntimeError
                       }
        audit_rpc.call(requestBody)
    except TypeError:
        # errror msg being sent to audit server
        requestBody = {"function": "ERROR_MESSAGE", "timeStamp": int(time.time() * 1000),
                       "server": "quoteServer", "transactionNum": payload.get('lineNum'),
                       "userId": payload.get('userId'),"command": payload.get("command"),
                       "errorMessage": TypeError
                       }
        audit_rpc.call(requestBody)
    except ArithmeticError:
        # errror msg being sent to audit server
        requestBody = {"function": "ERROR_MESSAGE", "timeStamp": int(time.time() * 1000),
                       "server": "quoteServer", "transactionNum": payload.get('lineNum'),
                       "userId": payload.get('userId'),"command": payload.get("command"),
                       "errorMessage": ArithmeticError
                       }
        audit_rpc.call(requestBody)



if __name__ == '__main__':
    quoteServer = Quotes()
    audit_rpc = AuditRpcClient()

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queueNames.QUOTE)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_request, queue=queueNames.QUOTE)

    print("awaiting quote requests")
    channel.start_consuming()
