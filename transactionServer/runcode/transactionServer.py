import math
import time
import json
from rabbitMQSetups import RabbitMQClient, RabbitMQReceiver, RabbitMQAyscClient , RabbitMQAyscReciever
from mqDatabaseServer import databaseFunctions
from mqQuoteServer import createQuoteRequest
from mqTriggers import TriggerFunctions
from mqAuditServer import auditFunctions
from threading import Thread
import multiprocessing
from multiprocessing import Process
from pprint import pprint

# userDisplaySummary shape: {userId: [command, command ...], ...}
class DisplaySummary():
    def __init__(self, max=10):
        self.max = max
        self.userDisplaySummary = {}

    def addCommand(self, command):
        userId = command["userId"]

        userSummary = self.userDisplaySummary.get(userId)
        if not userSummary:
            self.userDisplaySummary[userId] = []
            userSummary = self.userDisplaySummary[userId]

        userSummary.append(command)
        if len(userSummary) > self.max:
            del userSummary[0]

    def getDisplaySummary(self, userId):
        return self.userDisplaySummary.get(userId)


# quote shape: symbol: {value: string, retrieved: epoch time, user: string, cryptoKey: string}
class Quotes():
    def __init__(self, cacheExpire=60):
        self.cacheExpire = cacheExpire
        self.quoteCache = {}

    def getQuote(self, symbol):
        cache = self.quoteCache.get(symbol)
        if cache is not None:
            if self._cacheIsActive(cache):
                return cache
        return None

    def cacheQuote(self, symbol, retrieved, value):
        self.quoteCache[symbol] = {"retrieved": retrieved, "value": value}

    def useCache(self, quote, symbol, retrieved):
        print "-------"
        print "using quote cache"
        print quote, symbol, retrieved
        if quote is not None:
            print "caching quote"
            self.cacheQuote(symbol, retrieved, quote)
        else:
            print "no quote"
            localQuote = self.getQuote(symbol)
            print "local quote", localQuote
            if localQuote is not None:
                quote = localQuote["value"]
        print "returning", quote
        print "--------"
        return quote

    def _cacheIsActive(self, quote):
        print "checking cache active"
        print "retrieved:", int(quote.get('retrieved', 0)), "+", self.cacheExpire, "=", self.cacheExpire
        print "current:", int(time.time())
        print "active:", (int(quote.get('retrieved', 0)) + self.cacheExpire) > int(time.time())
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

        i = sum([ord(c) for c in symbol]) % 3
        quoteQueues[i].put(
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
        databaseQueue.put(
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
        databaseQueue.put(
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
        databaseQueue.put(
            databaseFunctions.createCommitBuyRequest(command, userId, buy, quote, transactionNum)
        )
    elif buy is not None:
        args["trans"] = RabbitMQClient.TRANSACTION

        i = sum([ord(c) for c in buy["symbol"]]) % 3
        quoteQueues[i].put(
            createQuoteRequest(userId, buy["symbol"], transactionNum, args)
        )
    else:
        databaseQueue.put(
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
        databaseQueue.put(
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
        databaseQueue.put(
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
        databaseQueue.put(
            databaseFunctions.createCommitSellRequest(command, userId, lineNum, sell, quote)
        )
    elif sell is not None:
        # have the sell, need to get a quote
        args["trans"] = RabbitMQClient.TRANSACTION

        i = sum([ord(c) for c in sell["symbol"]]) % 3
        quoteQueues[i].put(
            createQuoteRequest(userId, sell["symbol"], lineNum, args)
        )
    else:
        # this is where we need to go to the pop endpoint
        databaseQueue.put(
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
        databaseQueue.put(
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
        triggerQueue.put(
            TriggerFunctions.createAddBuyRequest(command, userId, symbol, amount, transactionNum)
        )
    else:
        databaseQueue.put(
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
        triggerQueue.put(
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
        databaseQueue.put(
            databaseFunctions.createReleaseCashRequest(command, userId, trigger["cashReserved"], symbol, transactionNum)
        )
    else:
         triggerQueue.put(
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
         triggerQueue.put(
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
         triggerQueue.put(
            TriggerFunctions.createSetSellActiveRequest(command, userId, symbol, sellAt, transactionNum)
        )
    elif sellTrigger is not None:
        reserve = math.floor(sellTrigger["maxSellAmount"] / sellAt)
        databaseQueue.put(
            databaseFunctions.createReservePortfolioRequest(command, userId, reserve, symbol, sellAt, transactionNum)
        )
    else:
         triggerQueue.put(
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
            databaseQueue.put(
                databaseFunctions.createReleasePortfolioRequest(command, userId, refund, symbol, transactionNum)
            )
        # if it wasnt active yet, nothing set aside, so we can just return
        else:
            return args
    else:
         triggerQueue.put(
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
    auditQueue.put(requestBody, 3)
    return "DUMPLOG SENT TO AUDIT"

def handleDisplaySummary(args):
    userId = args["userId"]

    buyTriggers = args.get("buyTriggers")
    sellTriggers = args.get("sellTriggers")

    user = args.get("user")
    print userId, buyTriggers, sellTriggers, user

    if user is not None:
        args["commandSummary"] = localDisplaySummary.getDisplaySummary(userId)
        return args
    elif (buyTriggers is not None) and (sellTriggers is not None):
        databaseFunctions.put(
            databaseFunctions.createSummaryRequest(userId, args)
        )
    else:
        triggerQueue.put(
            TriggerFunctions.createSummaryRequest(userId, args)
        )

    return None


def errorPrint(args, error):
    # let me push
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
        auditQueue.put(requestBody)

        returnClient = RabbitMQClient(queueName=RabbitMQClient.WEB + str(args['lineNum']))
        print "sending error back to webserver on queue: ", RabbitMQClient.WEB + str(args['lineNum'])
        returnClient.send(
            create_response(args.get("response"), args)
        )
        print "error sent to webserver"
        returnClient.close()
        return
    else:
        try:
            # send command to audit, if it is from web server
            if prop == 1 or prop == 3:
                if args["command"] != "DUMPLOG":
                    # add command to local memory for the user
                    localDisplaySummary.addCommand(args)

                    # send command to audit
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
                    auditQueue.put(requestBody)

                else:
                    requestBody = auditFunctions.createUserCommand(
                        int(time.time() * 1000),
                        "transactionServer",
                        args["lineNum"],
                        args["userId"],
                        args["command"],
                        args.get("stockSymbol"),
                        args.get("fileName"),
                        args.get("cash")
                    )
                    # Log User Command Call of DUMPLOG
                    auditQueue.put(requestBody)

            # Sanitizing for Negative values of cash
            if args.get("cash") != None and args.get("cash") < 0:
                returnClient = RabbitMQClient(queueName=RabbitMQClient.WEB + str(args['lineNum']))
                returnClient.send(
                    create_response(400, "invalid arguments" + str(args))
                )
                returnClient.close()
                return
            function = functionSwitch.get(args["command"])
            if function:
                # if a function is complete, it should return a response to send back to web server
                # if it is not complete (needs to go to another service) it should return None
                response = function(args)
                print "response from call:", response
                if response.get('lineNum') <= 0:
                    print "return response to webserver: ", response
                    returnClient = RabbitMQClient(queueName=RabbitMQClient.WEB+str(response["lineNum"]))
                    print "created the return client"
                    returnClient.send(
                        create_response(200, response)
                    )
                    print "sent the message back"
                    returnClient.close()
                    print "closed the return client"
                return
            else:
                print "couldn't figure out command...", args
                if args.get('lineNum') <= 0:
                    returnClient = RabbitMQClient(queueName=RabbitMQClient.WEB+str(args['lineNum']))
                    returnClient.send(
                         create_response(404, "function not found" + str(args))
                    )
                    returnClient.close()
                return
        except (RuntimeError, TypeError, ArithmeticError, KeyError) as error:
            print "before error print here"
            errorPrint(args, error)
            requestBody = auditFunctions.createErrorMessage(
                int(time.time() * 1000),
                "transactionServer",
                args["lineNum"],
                args["userId"],
                args["command"],
                str(error)
            )
            auditQueue.put(requestBody)
            if args.get('lineNum') <= 0:
                returnClient = RabbitMQClient(queueName=RabbitMQClient.WEB+str(args['lineNum']))
                returnClient.send(
                    create_response(500, args)
                )
                returnClient.close()
            return


if __name__ == '__main__':
    print "starting TransactionServer"


    localQuoteCache = Quotes()
    localDisplaySummary = DisplaySummary()

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
        "DUMPLOG": handleCommandDumplog,
        "DISPLAY_SUMMARY": handleDisplaySummary
    }


    #
    # quoteClient = RabbitMQClient(RabbitMQClient.QUOTE)
    # auditClient = RabbitMQClient(RabbitMQClient.AUDIT)
    # databaseClient = RabbitMQClient(RabbitMQClient.DATABASE)
    # triggerClient = RabbitMQClient(RabbitMQClient.TRIGGERS)

    print "create Auditpublisher"
    auditQueue = multiprocessing.Queue()
    audit_producer_process = Process(target=RabbitMQAyscClient,
                                     args=( RabbitMQAyscClient.AUDIT , auditQueue))
    audit_producer_process.start()

    print "create Quotepublisher1"
    quoteQueue1 = multiprocessing.Queue()
    quote_producer_process1 = Process(
        target=RabbitMQAyscClient,
        args=( RabbitMQAyscClient.QUOTE1, quoteQueue1)
    )
    quote_producer_process1.start()

    print "create Quotepublisher2"
    quoteQueue2 = multiprocessing.Queue()
    quote_producer_process2 = Process(
        target=RabbitMQAyscClient,
        args=(RabbitMQAyscClient.QUOTE2, quoteQueue2)
    )
    quote_producer_process2.start()

    print "create Quotepublisher3"
    quoteQueue3 = multiprocessing.Queue()
    quote_producer_process3 = Process(
        target=RabbitMQAyscClient,
        args=(RabbitMQAyscClient.QUOTE3, quoteQueue3)
    )
    quote_producer_process3.start()

    quoteQueues = [quoteQueue1, quoteQueue2, quoteQueue3]

    print "create Triggerpublisher"
    triggerQueue = multiprocessing.Queue()
    trigger_producer_process = Process(target=RabbitMQAyscClient,
                                     args=(  RabbitMQAyscClient.TRIGGERS, triggerQueue ))
    trigger_producer_process.start()

    print "create databasepublisher"
    databaseQueue = multiprocessing.Queue()
    database_producer_process = Process(target=RabbitMQAyscClient,
                                     args=( RabbitMQAyscClient.DATABASE, databaseQueue))
    database_producer_process.start()

    # This is the new python in memory queue for the transation Server to eat from.

    # Adding in multiProcessing
    print "trying to start PQ"
    # rabbit = rabbitQueue()
    print "registered PQ"

    P1Q_rabbit = multiprocessing.Queue()
    P2Q_rabbit = multiprocessing.Queue()
    P3Q_rabbit = multiprocessing.Queue()


    print "Created multiprocess PriorityQueues"
    consumer_process = Process(target=RabbitMQAyscReciever, args=(RabbitMQAyscReciever.TRANSACTION , P1Q_rabbit , P2Q_rabbit , P3Q_rabbit))
    consumer_process.start()
    print "Created multiprocess Consummer"

    while(True):
        try:
            msg = P2Q_rabbit.get(False)
            if msg:
                payload = msg[1]
                props = msg[0]
                print "queue size: ", P2Q_rabbit.qsize()
                delegate(None, None, props, payload)
                continue
        except:
            pass
        try:
            msg = P1Q_rabbit.get(False)
            if msg:
                payload = msg[1]
                props = msg[0]
                print "queue size: ", P1Q_rabbit.qsize()
                delegate(None, None, props, payload)
                continue
        except:
            pass
        try:
            msg = P3Q_rabbit.get(False)
            if msg:
                payload = msg[1]
                props = msg[0]
                print "queue size: ", P3Q_rabbit.qsize()
                delegate(None, None, props, payload)
        except:
            pass
            #         queue is empty

