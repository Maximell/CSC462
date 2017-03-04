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


# From webServer: {"transactionNum": lineNum, "command": "QUOTE", "userId": userId, "stockSymbol": stockSymbol}
# From quoteServer: + "quote:, "cryptoKey"
def handleCommandQuote(args):
    symbol = args["stockSymbol"]
    userId = args["userId"]
    lineNum = args["lineNum"]

    quote = args.get("quote")
    cryptoKey = args.get("cryptoKey")

    if quote and cryptoKey:
        print "Quote return: ", args
        return args
    else:
        quoteClient.send(
            createQuoteRequest(userId, symbol, lineNum, args)
        )
        return None


def handleCommandAdd(args):
    command = args["command"]
    userId = args["userId"]
    lineNum = args["lineNum"]
    cash = args["cash"]

    reserve = args.get("reserve")

    # if the command has 'reserve' associated with it, then it is being returned from the db
    if reserve:
        return args
    else:
        databaseClient.send(
            databaseFunctions.createAddRequest(command, userId, lineNum, cash)
        )
        return None


def handleCommandBuy(args):
    command = args['command']
    lineNum = args['lineNum']
    symbol = args['stockSymbol']
    cash = args['cash']
    userId = args['userId']

    # if response, this means it has already been to the DB
    # a response of 200 means success, 400 means not enough cash for buy
    if args.get('response'):
        return args
    else:
        databaseClient.send(
            databaseFunctions.createBuyRequest(command, userId, lineNum, cash, symbol)
        )
        return None


def handleCommandCommitBuy(args):
    userId = args["userId"]
    transactionNum = args["lineNum"]

    buy = args.get("buy")
    quote = args.get("quote")

    if buy and quote:
        return args
    elif buy:
        quoteClient.send(
            createQuoteRequest(userId, buy["symbol"], transactionNum, args)
        )
    else:
        databaseClient.send(
            databaseFunctions.createPopBuyRequest(userId, transactionNum)
        )
    return None


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
    requestBody = auditFunctions.createWriteLogs(
        int(time.time() * 1000),
        "transactionServer",
        args["lineNum"],
        args["userId"],
        args["command"]
    )
    auditClient.send(requestBody)


def errorPrint(args, error):
    print "-------ERROR-------"
    print "args:", args
    print "error:", error
    print "-------------------"


def create_response(status, response):
    return {'status': status, 'body': response}


def delegate(ch , method, properties, body):
    args = ast.literal_eval(body)
    print "incoming args: ", args

    # error checking from other components
    if args.get("response") >= 400:
        error = str(args.get("response")) + ": " + str(args.get("errorString"))

        errorPrint(args, error)
        requestBody = auditFunctions.createErrorMessage(
            int(time.time() * 1000),
            "transactionServer",
            args["lineNum"],
            args["userId"],
            args["command"],
            error
        )
        auditClient.send(requestBody)

        create_response(args.get("response"), str(args.get("errorString")))
        # TODO: return this ^ to the webserver (through a rabbitClient)
    else:
        try:
            # send command to audit
            if args["userId"] != "./testLOG":
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
                auditClient.send(requestBody)

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
                auditClient.send(requestBody)

            function = functionSwitch.get(args["command"])
            if function:
                # if a function is complete, it should return a response to send back to web server
                # if it is not complete (needs to go to another service) it should return None
                response = function(args)
                if response is not None:
                    create_response(200, response)
                    # TODO: return this ^ to the webserver (through a rabbitClient)
            else:
                print "couldn't figure out command...", args
                create_response(404, "function not found" + str(args))
                # TODO: return this ^ to the webserver (through a rabbitClient)

        except (RuntimeError, TypeError, ArithmeticError, KeyError) as error:
            errorPrint(args, error)
            requestBody = auditFunctions.createErrorMessage(
                int(time.time() * 1000),
                "transactionServer",
                args["lineNum"],
                args["userId"],
                args["command"],
                str(error)
            )
            auditClient.send(requestBody)
            create_response(500, str(error))
            # TODO: return this ^ to the webserver (through a rabbitClient)


if __name__ == '__main__':
    print "starting TransactionServer"

    functionSwitch = {
        "QUOTE": handleCommandQuote,
        "ADD": handleCommandAdd,
        "BUY": handleCommandBuy,
        "COMMIT_BUY": handleCommandCommitBuy,
        "CANCEL_BUY": handleCommandCancelBuy,
        "SELL": handleCommandSell,
        "COMMIT_SELL": handleCommandCommitSell,
        # "CANCEL_SELL": handleCommandCancelSell,
        # "SET_BUY_AMOUNT": handleCommandSetBuyAmount,
        # "CANCEL_BUY_AMOUNT": handleCommandCancelSetBuy,
        # "SET_BUY_TRIGGER": handleCommandSetBuyTrigger,
        # "SET_SELL_AMOUNT": handleCommandSetSellAmount,
        # "CANCEL_SELL_AMOUNT": handleCommandCancelSetSell,
        "SET_SELL_TRIGGER": handleCommandSetSellTrigger,
        "DUMPLOG": handleCommandDumplog
    }

    # rpc classes
    #quote_rpc = QuoteRpcClient()
    #db_rpc = DatabaseRpcClient()
    trigger_rpc = TriggerRpcClient()

    quoteClient = RabbitMQClient(RabbitMQClient.QUOTE)
    auditClient = RabbitMQClient(RabbitMQClient.AUDIT)
    databaseClient = RabbitMQClient(RabbitMQClient.DATABASE)

    RabbitMQReceiver(delegate, RabbitMQReceiver.TRANSACTION)
