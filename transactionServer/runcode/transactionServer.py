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

    if (quote is not None) and cryptoKey:
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
    if reserve is not None:
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
    if args.get('response') is not None:
        return args
    else:
        databaseClient.send(
            databaseFunctions.createBuyRequest(command, userId, lineNum, cash, symbol)
        )
        return None


def handleCommandCommitBuy(args):
    command = args['command']
    userId = args["userId"]
    transactionNum = args["lineNum"]

    buy = args.get("buy")
    quote = args.get("quote")
    updatedUser = args.get("updatedUser")

    if updatedUser is not None:
        return args
    elif (buy is not None) and (quote is not None):
        databaseClient.send(
            databaseFunctions.createCommitBuyRequest(command, userId, buy, quote, transactionNum)
        )
    elif buy is not None:
        quoteClient.send(
            createQuoteRequest(userId, buy["symbol"], transactionNum, args)
        )
    else:
        databaseClient.send(
            databaseFunctions.createPopBuyRequest(command, userId, transactionNum)
        )
    return None


def handleCommandCancelBuy(args):
    command = args['command']
    userId = args["userId"]
    transactionNum = args["lineNum"]

    buy = args.get("buy")

    if buy is not None:
        return args
    else:
        databaseClient.send(
            databaseFunctions.createCancelBuyRequest(command, userId, transactionNum)
        )
    return None


def handleCommandSell(args):
    command = args["command"]
    userId = args["userId"]
    lineNum = args["lineNum"]
    stockSymbol = args["stockSymbol"]
    cash = args["cash"]

    # if response, has already been to DB
    # response of 200 means success, 400 means not enough of that stock
    if args.get("response") is not None:
        return args
    else:
        databaseClient.send(
            databaseFunctions.createSellRequest(command, userId, lineNum, cash, stockSymbol)
        )
    return None


def handleCommandCommitSell(args):
    command = args["command"]
    userId = args["userId"]
    lineNum = args["lineNum"]

    sell = args.get("sell")
    updatedUser = args.get("updatedUser")
    quote = args.get("quote")

    if updatedUser is not None:
        return args
    elif (sell is not None) and (quote is not None):
        # this is where we commit the sell
        databaseClient.send(
            databaseFunctions.createCommitSellRequest(command, userId, lineNum, sell, quote)
        )
    elif sell is not None:
        # have the sell, need to get a quote
        quoteClient.send(
            createQuoteRequest(userId, sell["symbol"], lineNum, args)
        )
    else:
        # this is where we need to go to the pop endpoint
        databaseClient.send(
            databaseFunctions.createPopSellRequest(command, userId, lineNum)
        )
    return None


def handleCommandCancelSell(args):
    command = args["command"]
    userId = args["userId"]
    lineNum = args["lineNum"]

    sell = args.get("sell")

    if sell is not None:
        return args
    else:
        databaseClient.send(
            databaseFunctions.createCancelSellRequest(command, userId, lineNum)
        )
    return None


def handleCommandSetBuyAmount(args):
    command = args["command"]
    symbol = args["stockSymbol"]
    amount = args["cash"]
    userId = args["userId"]
    transactionNum = args["lineNum"]

    reserved = args.get("reserve")
    trigger = args.get("trigger")

    if trigger is not None:
        return args
    elif reserved is not None:
        triggerClient.send(
            TriggerFunctions.createAddBuyRequest(command, userId, symbol, amount, transactionNum)
        )
    else:
        databaseClient.send(
            databaseFunctions.createReserveCashRequest(command, userId, amount, symbol, transactionNum)
        )
    return None


def handleCommandSetBuyTrigger(args):
    command = args["command"]
    symbol = args["stockSymbol"]
    buyAt = args["cash"]
    userId = args["userId"]
    transactionNum = args["lineNum"]

    trigger = args.get("trigger")

    if trigger is not None:
        return args
    else:
        triggerClient.send(
            TriggerFunctions.createSetBuyActiveRequest(command, userId, symbol, buyAt, transactionNum)
        )
    return None


def handleCommandCancelSetBuy(args):
    command = args["command"]
    symbol = args["stockSymbol"]
    userId = args["userId"]
    transactionNum = args["lineNum"]

    trigger = args.get("trigger")
    cash = args.get("cash")

    if cash is not None:
        return args
    elif trigger is not None:
        databaseClient.send(
            databaseFunctions.createReleaseCashRequest(command, userId, trigger["cashReserved"], symbol, transactionNum)
        )
    else:
        triggerClient.send(
            TriggerFunctions.createCancelBuyRequest(command, userId, symbol, transactionNum)
        )
    return None


def handleCommandSetSellAmount(args):
    command = args["command"]
    symbol = args["stockSymbol"]
    amount = args["cash"]
    userId = args["userId"]
    transactionNum = args["lineNum"]

    trigger = args.get("trigger")
    if trigger is not None:
        return args
    else:
        triggerClient.send(
            TriggerFunctions.createAddSellRequest(command, userId, symbol, amount, transactionNum)
        )
    return None


def handleCommandSetSellTrigger(args):
    command = args["command"]
    symbol = args["stockSymbol"]
    sellAt = args["cash"]
    userId = args["userId"]
    transactionNum = args["lineNum"]

    sellTrigger = args.get("sellTrigger")
    reservedPortfolio = args.get("reservedPortfolio")
    trigger = args.get("trigger")

    if trigger is not None:
        return args
    elif reservedPortfolio:
        triggerClient.send(
            TriggerFunctions.createSetSellActiveRequest(command, userId, symbol, sellAt, transactionNum)
        )
    elif sellTrigger is not None:
        reserve = math.floor(sellTrigger["maxSellAmount"] / sellAt)
        databaseClient.send(
            databaseFunctions.createReservePortfolioRequest(command, userId, reserve, symbol, sellAt, transactionNum)
        )
    else:
        triggerClient.send(
            TriggerFunctions.createGetSellRequest(command, userId, symbol, sellAt, transactionNum)
        )

    return None


def handleCommandCancelSetSell(args):
    command = args["command"]
    symbol = args["stockSymbol"]
    userId = args["userId"]
    transactionNum = args["lineNum"]

    trigger = args.get("trigger")
    portfolioAmount = args.get("portfolioAmount")

    if portfolioAmount is not None:
        return args
    elif trigger is not None:
        # if the removed trigger was active, then we set aside portfolio for it
        if trigger["active"]:
            refund = math.floor(trigger["maxSellAmount"] / trigger["sellAt"])
            databaseClient.send(
                databaseFunctions.createReleasePortfolioRequest(command, userId, refund, symbol, transactionNum)
            )
        # if it wasnt active yet, nothing set aside, so we can just return
        else:
            return args
    else:
        triggerClient.send(
            TriggerFunctions.createCancelSellRequest(command, userId, symbol, transactionNum)
        )

    return None


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
    args = json.loads(body)
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
            # send command to audit, if it is from web server
            if properties.priority == 1:
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
                    returnClient = RabbitMQClient(queueName=RabbitMQClient.WEB+str(response["lineNum"]))
                    returnClient.send(
                        create_response(200, response)
                    )
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
        "CANCEL_SELL": handleCommandCancelSell,
        "SET_BUY_AMOUNT": handleCommandSetBuyAmount,
        "CANCEL_SET_BUY": handleCommandCancelSetBuy,
        "SET_BUY_TRIGGER": handleCommandSetBuyTrigger,
        "SET_SELL_AMOUNT": handleCommandSetSellAmount,
        "CANCEL_SET_SELL": handleCommandCancelSetSell,
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
    triggerClient = RabbitMQClient(RabbitMQClient.TRIGGERS)

    RabbitMQReceiver(delegate, RabbitMQReceiver.TRANSACTION)
