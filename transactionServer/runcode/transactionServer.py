import math
import time
import uuid
import pika
import json
import ast
from rabbitMQSetups import RabbitMQClient, RabbitMQReceiver
from mqDatabaseServer import databaseFunctions
from mqQuoteServer import createQuoteRequest
from mqTriggers import TriggerFunctions
from mqAuditServer import auditFunctions


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
            routing_key=RabbitMQClient.AUDIT,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body=json.dumps(requestBody)
        )
        while self.response is None:
            self.connection.process_data_events()
        print "From Audit server: ", self.response
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
            routing_key=RabbitMQClient.QUOTE,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body=json.dumps(requestBody)
        )
        while self.response is None:
            self.connection.process_data_events()
        print "From Quote server: ",  self.response
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
            routing_key=RabbitMQClient.DATABASE,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body=json.dumps(requestBody)
        )
        while self.response is None:
            self.connection.process_data_events()
        print "From Database server: ",  self.response
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
        print "sending Trigger request Id:", self.corr_id , requestBody
        self.channel.basic_publish(
            exchange='',
            routing_key=RabbitMQClient.TRIGGERS,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body=json.dumps(requestBody)
        )
        while self.response is None:
            self.connection.process_data_events()
        print "From Trigger server: ",  self.response
        return self.response


def delegate(ch , method, properties, body):
    args = ast.literal_eval(body)
    print args
    try:
        if "./testLOG" != args["userId"]:

            requestBody = auditFunctions.createUserCommand(
                int(time.time() * 1000),
                "transactionServer",
                args["lineNum"],
                args["userId"],
                args["command"],
                args.get("stockSymbol"),
                None,
                args.get("cash")
            )
            # Log User Command Call
            audit_rpc.call(requestBody)

        else:
            requestBody = auditFunctions.createUserCommand(
                int(time.time() * 1000),
                "transactionServer",
                args["lineNum"],
                args["userId"],
                args["command"],
                args.get("stockSymbol"),
                args["userId"],
                args.get("cash")
            )
            # Log User Command Call
            audit_rpc.call(requestBody)

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

        # elif args["command"] == "SET_BUY_AMOUNT":
        #     handleCommandSetBuyAmount(args)
        #
        # elif args["command"] == "CANCEL_BUY_AMOUNT":
        #     handleCommandCancelSetBuy(args)
        #
        # elif args["command"] == "SET_BUY_TRIGGER":
        #     handleCommandSetBuyTrigger(args)
        #
        # elif args["command"] == "SET_SELL_AMOUNT":
        #     handleCommandSetSellAmount(args)
        #
        # elif args["command"] == "CANCEL_SELL_AMOUNT":
        #     handleCommandCancelSetSell(args)
        #
        # elif args["command"] == "SET_SELL_TRIGGER":
        #     handleCommandSetSellTrigger(args)
        elif args["command"] == "DUMPLOG":
            handleCommandDumplog(args)
        else:
            print "couldn't figure out command..."
            print "command: ", args
    except RuntimeError:
        requestBody = auditFunctions.createErrorMessage(
            int(time.time() * 1000),
            "transactionServer",
            args["lineNum"],
            args["userId"],
            args["command"],
            str(RuntimeError)
        )
        audit_rpc.call(requestBody)
    except TypeError:
        # errror msg being sent to audit server
        requestBody = auditFunctions.createErrorMessage(
            int(time.time() * 1000),
            "transactionServer",
            args["lineNum"],
            args["userId"],
            args["command"],
            str(TypeError)
        )
        audit_rpc.call(requestBody)
    except ArithmeticError:
        # errror msg being sent to audit server
        requestBody = auditFunctions.createErrorMessage(
            int(time.time() * 1000),
            "transactionServer",
            args["lineNum"],
                args["userId"],
            args["command"],
            str(ArithmeticError)
        )
        audit_rpc.call(requestBody)

# From webServer: {"transactionNum": lineNum, "command": "QUOTE", "userId": userId, "stockSymbol": stockSymbol}
# From quoteServer: + "quote:, "cryptoKey"
def handleCommandQuote(args):
    symbol = args["stockSymbol"]
    userId = args["userId"]
    transactionNum = args["transactionNum"]

    if args.get("quote") and args.get("cryptoKey"):
        pass #TODO: Add return to webServer
    else:
        quoteClient.send(
            createQuoteRequest(userId, symbol, transactionNum)
        )


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
    transactionNum = args["lineNum"]

    popRequest = databaseFunctions.createPopBuyRequest(userId)
    popResponse = db_rpc.call(popRequest)
    if popResponse["status"] == 200:
        buy = popResponse["body"]
        quote = createQuoteRequest(userId, buy["symbol"], transactionNum)
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
    transactionNum = args["lineNum"]

    popRequest = databaseFunctions.createPopSellRequest(userId)
    popResponse = db_rpc.call(popRequest)
    if popResponse["status"] == 200:
        sell = popResponse["body"]
        quote = createQuoteRequest(userId, sell["symbol"], transactionNum)
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
    transactionNum = args.get("lineNum")

    reserveRequest = databaseFunctions.createReserveCashRequest(userId, amount)
    reserveResponse = db_rpc.call(reserveRequest)
    if reserveResponse["status"] == 200:
        buyRequest = TriggerFunctions.createAddBuyRequest(userId, symbol, amount, transactionNum)
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
    transactionNum = args.get("lineNum")

    sellRequest = TriggerFunctions.createAddSellRequest(userId, symbol, amount, transactionNum)
    sellResponse = trigger_rpc.call(sellRequest)


def handleCommandSetSellTrigger(args):
    symbol = args.get("stockSymbol")
    sellAt = args.get("cash")
    userId = args.get("userId")

    getTriggerRequest = TriggerFunctions.createGetSellRequest(userId, symbol)
    getTriggerResponse = trigger_rpc.call(getTriggerRequest)
    if getTriggerResponse["status"] == 200:
        trigger = getTriggerResponse["body"]
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

def handleCommandDumplog(args):
    requestBody = auditFunctions.createWriteLogs(int(time.time() * 1000), "transactionServer", args["lineNum"],
                                                 args["userId"], args["command"])
    audit_rpc.call(requestBody)


def listenToRabbitQ():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=RabbitMQClient.WEBSERVER)
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
    print "starting TransactionServer"

    quoteClient = RabbitMQClient(RabbitMQClient.QUOTE)
    RabbitMQReceiver(delegate, RabbitMQReceiver.TRANSACTION)

    # rpc classes
    audit_rpc = AuditRpcClient()
    quote_rpc = QuoteRpcClient()
    db_rpc = DatabaseRpcClient()
    trigger_rpc = TriggerRpcClient()

    main()
