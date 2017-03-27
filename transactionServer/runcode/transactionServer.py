import math
import time
import json
from rabbitMQSetups import RabbitMQClient, RabbitMQReceiver
from mqDatabaseServer import databaseFunctions
from mqQuoteServer import createQuoteRequest
from mqTriggers import TriggerFunctions
from mqAuditServer import auditFunctions
from threading import Thread
import Queue

class rabbitQueue:
    def __init__(self):
        self.queue = Queue.PriorityQueue()

class consumer (Thread):
    def __init__(self , queueName):
        Thread.__init__(self)
        self.daemon = True
        self.queueName = queueName
        self.start()
        # self.join()

    def run(self):
        print "started"
        rabbitConsumer(self.queueName)


class rabbitConsumer():
    def __init__(self, queueName):
        self.connection = RabbitMQReceiver(self.consume, queueName)

    def consume(self, ch, method, props, body):
        payload = json.loads(body)
        line = payload.get("lineNum")
        if line is None:
            line = payload.get("transactionNum")

        if props.priority == 1:
            # flipping priority b/c Priority works lowestest to highest
            # But our system works the other way.

            # We need to display lineNum infront of payload to so get() works properly
            rabbit.queue.put((2, [line, payload]))
        elif props.priority == 2:
            rabbit.queue.put((1, [line, payload]))
        else:
            rabbit.queue.put((3, [line, payload]))


# quote shape: symbol: {value: string, retrieved: epoch time, user: string, cryptoKey: string}
class Quotes():
    def __init__(self, cacheExpire=60):
        self.cacheExpire = cacheExpire
        self.quoteCache = {}

    def getQuote(self, symbol):
        cache = self.quoteCache.get(symbol)
        if cache:
            if self._cacheIsActive(cache):
                return cache
        return None

    def cacheQuote(self, symbol, retrieved, value):
        self.quoteCache[symbol] = {"retrieved": retrieved, "value": value}

    def useCache(self, quote, symbol, retrieved):
        if quote is not None:
            self.cacheQuote(symbol, retrieved, quote)
        else:
            localQuote = self.getQuote(symbol)
            if localQuote is not None:
                quote = localQuote["value"]
        return quote

    def _cacheIsActive(self, quote):
        return (int(quote.get('retrieved', 0)) + self.cacheExpire) > int(time.time())


# From webServer: {"transactionNum": lineNum, "command": "QUOTE", "userId": userId, "stockSymbol": stockSymbol}
# From quoteServer: + "quote:, "cryptoKey"
def handleCommandQuote(args):
    symbol = args["stockSymbol"]
    userId = args["userId"]
    lineNum = args["lineNum"]

    quote = localQuoteCache.useCache(
        args.get("quote"),
        symbol,
        args.get("quoteRetrieved")
    )

    if quote is not None:
        print "Quote return: ", args
        return args
    else:
        args["trans"] = RabbitMQClient.TRANSACTION
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
    updatedUser = args.get("updatedUser")

    if buy is not None:
        quote = localQuoteCache.useCache(
            args.get("quote"),
            buy["symbol"],
            args.get("quoteRetrieved")
        )

    if updatedUser is not None:
        return args
    elif (buy is not None) and (quote is not None):
        databaseClient.send(
            databaseFunctions.createCommitBuyRequest(command, userId, buy, quote, transactionNum)
        )
    elif buy is not None:
        args["trans"] = RabbitMQClient.TRANSACTION
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
    if sell is not None:
        quote = localQuoteCache.useCache(
            args.get("quote"),
            sell["symbol"],
            args.get("quoteRetrieved")
        )

    if updatedUser is not None:
        return args
    elif (sell is not None) and (quote is not None):
        # this is where we commit the sell
        databaseClient.send(
            databaseFunctions.createCommitSellRequest(command, userId, lineNum, sell, quote)
        )
    elif sell is not None:
        # have the sell, need to get a quote
        args["trans"] = RabbitMQClient.TRANSACTION
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
    auditClient.send(requestBody, 3)


def errorPrint(args, error):
    print "-------ERROR-------"
    print "args:", args
    print "error:", error
    print "-------------------"


def create_response(status, response):
    return {'status': status, 'body': response}


def delegate(ch , method, prop, args):
    # args = json.loads(body)
    print "incoming args: ", args
    print prop

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
        # auditClient.send(requestBody)

        returnClient = RabbitMQClient(queueName=RabbitMQClient.WEB + str(args['lineNum']))
        print "sending error back to webserver on queue: ", RabbitMQClient.WEB + str(args['lineNum'])
        returnClient.send(
            create_response(args.get("response"), args)
        )
        print "error sent to webserver"
        returnClient.close()
    else:
        try:
            # send command to audit, if it is from web server
            if prop == 2:
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

            # Sanitizing for Negative values of cash
            if args.get("cash") != None and args.get("cash") > 0:
                returnClient = RabbitMQClient(queueName=RabbitMQClient.WEB + str(args['lineNum']))
                returnClient.send(
                    create_response(400, "invalid arguments" + str(args))
                )
                returnClient.close()

            function = functionSwitch.get(args["command"])
            if function:
                # if a function is complete, it should return a response to send back to web server
                # if it is not complete (needs to go to another service) it should return None
                response = function(args)
                print "response from call:", response
                if response is not None:
                    print "return response to webserver: ", response
                    returnClient = RabbitMQClient(queueName=RabbitMQClient.WEB+str(response["lineNum"]))
                    returnClient.send(
                        create_response(200, response)
                    )
                    returnClient.close()
            else:
                print "couldn't figure out command...", args
                returnClient = RabbitMQClient(queueName=RabbitMQClient.WEB+str(args['lineNum']))
                returnClient.send(
                    create_response(404, "function not found" + str(args))
                )
                returnClient.close()

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
            # auditClient.send(requestBody)
            returnClient = RabbitMQClient(queueName=RabbitMQClient.WEB+str(args['lineNum']))
            returnClient.send(
                create_response(500, args)
            )
            returnClient.close()


if __name__ == '__main__':
    print "starting TransactionServer"

    localQuoteCache = Quotes()

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



    quoteClient = RabbitMQClient(RabbitMQClient.QUOTE)
    auditClient = RabbitMQClient(RabbitMQClient.AUDIT)
    databaseClient = RabbitMQClient(RabbitMQClient.DATABASE)
    triggerClient = RabbitMQClient(RabbitMQClient.TRIGGERS)

    # This is the new python in memory queue for the transation Server to eat from.
    rabbit = rabbitQueue()
    consumeRabbit = consumer(RabbitMQReceiver.TRANSACTION)
    print "made thread"
    while(True):
        if rabbit.queue.empty():
            # print "empty"
            continue
        else:
            msg = rabbit.queue.get()
            payload = msg[1]
            args = payload[1]
            props = msg[0]
            print "queue size: ", rabbit.queue.qsize()
            delegate(None, None, props, args)

