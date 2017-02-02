# demonstrate talking to the quote server
import math
import socket
import time
import urlparse
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import BaseServer

from OpenSSL import SSL


# from events import Event



# COMMANDS NEEDED
#
# add
#
# quote j
# buy
# commit_buy
# cancel_buy
# sell
# commit_sell
# cancel_sell
#
# set_buy_amount
# cancel_set_buy
# set_buy_trigger
#
# set_sell_amount
# cancel_set_sell
# set_sell_trigger
#
# dumplog    (x2)
# display_summary

# general structure of endpoints
# Add:
#   databaseServer.getOrAddUser
#
# Quote:
#   quotes.getQuote
#
# Buy:
#   quotes.getQuote
#   databaseServer.pushBuy
#   databaseServer.reserveCash
#
# Cancel buy:
#   databaseServer.popBuy
#   databaseServer.releaseCash
#
# Commit buy:
#   databaseServer.popBuy
#   databaseServer.isBuySellActive
#   databaseServer.addToPortfolio
#   databaseServer.missingFunctionForTakeCash
#
# Sell:
# quotes.getQuote
#   databaseServer.pushSell
#
# Cancel Sell:
#   databaseServer.popSell
#
# commit Sell:
#   databaseServer.popSell
#   databaseServer.isBuySellActive
#   databaseServer.removeFromPortfolio
#   databaseServer.addCash

#
# class events:
#     systemEvent
#     accountTransaction
#     commandEvent - this adds a method for each type of command
#         userCommand
#         quoteServer
#         errorEvent
#
# method add arguments


class httpsServer(HTTPServer):
    def __init__(self, serverAddr, handlerClass):
        BaseServer.__init__(self, serverAddr, handlerClass)
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        # server.pem's location (containing the server private key and
        # the server certificate).
        fpem = "cert.pem"
        ctx.use_privatekey_file(fpem)
        ctx.use_certificate_file(fpem)
        self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
                                                        self.socket_type))
        self.server_bind()
        self.server_activate()

    def shutdown_request(self, request):
        request.shutdown()
        # def parse_request(self , request):
        #     print "servicing"


class httpsRequestHandler(SimpleHTTPRequestHandler):
    def setup(self):
        self.connection = self.request
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)
        self.rfile = socket._fileobject(self.request, "rb", self.wbufsize)

    def do_GET(self):
        # print self.command
        self.send_response(200)

    def do_POST(self):
        try:
            if self.request != None:
                self.handle()
                self.send_response(200)

            else:
                self.send_response(400)
        except:
            self.handle_error()

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        # just send back the same data, but upper-cased
        self.request.send(self.data.upper())
        extractData(self.data)


def extractData(data):
    # extracting data and splitting properly

    args = urlparse.parse_qs(data)
    # print args
    splitInfo = args["args"][0].split()
    sanitized = []
    # removing chars to make args easier to deal with
    # in the future
    for x in splitInfo:
        x = x.strip('[')
        x = x.strip(']')
        x = x.strip('\'')
        x = x.strip(',')
        x = x.strip('\'')
        sanitized.append(x)

    args["userId"] = sanitized[0]
    args["command"] = args["command"][0]
    # extracting the line number
    for key, value in args.iteritems():
        string = str(key[0]) + str(key[1]) + str(key[2]) + str(key[3])
        if string == "POST":
            args["lineNum"] = value[0]
            del args[key]
            break

    # depending on what command we have
    if len(sanitized) == 2:
        # 2 case: 1 where userId and sym
        #         2 where userId and cash
        if args["command"] == 'ADD':
            args["cash"] = sanitized[1]
        else:
            args["sym"] = sanitized[1]
    if len(sanitized) == 3:
        args["sym"] = sanitized[1]
        args["cash"] = float(sanitized[2])

    del args["args"]
    # args now has keys: userId , sym , lineNUM , command , cash
    #
    # {'userId': 'oY01WVirLr', 'cash': '63511.53',
    # 'lineNum': '1', 'command': 'ADD'}

    '''
        This should be changed to use the Events class - when it is done.
    '''

    delegate(args)


def delegate(args):
    # this is where we will figure what command we are dealing with
    # and deligate from here to whatever function is needed
    # to handle the request
    # ----------------------------
    # add
    # quote
    # buy
    # commit_buy
    # cancel_buy
    # sell
    # commit_sell
    # cancel_sell
    #
    # set_buy_amount
    # cancel_set_buy
    # set_buy_trigger
    #
    # set_sell_amount
    # cancel_set_sell
    # set_sell_trigger
    # ----------------------------



    # Call Quote
    if "./testLOG" != args["userId"]:
        # TODO: not sure how filename comes in
        auditServer.logUserCommand(
            int(time.time() * 1000),
            "transaction",
            args.get('lineNum'),
            args.get('userId'),
            args.get("command"),
            stockSymbol=args.get('sym'),
            fileName=None,
            amount=args.get('cash')
        )
        localDB.addUser(args["userId"])
    else:
        # TODO: not sure how filename comes in
        fileName = args.get('userId')
        auditServer.logUserCommand(
            int(time.time() * 1000),
            "transaction",
            args.get('lineNum'),
            "TODO get user properly",
            args.get("command"),
            stockSymbol=args.get('sym'),
            fileName=fileName,
            amount=args.get('cash')
        )
        auditServer.writeLogs(fileName)



    if args["command"] == "QUOTE":
        # print "getting Quote"
        quoteObj.getQuote(args["sym"], args["userId"], args["lineNum"])
        # quoteObj._printQuoteCacheState()

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

    # triggers
    elif args["command"] == "SET_BUY_AMOUNT":
        handleCommandSetBuyAmount(args)

    elif args["command"] == "CANCEL_BUY_AMOUNT":
        handleCommandCancelSetBuy(args)

    elif args["command"] == "SET_BUY_TRIGGER":
        handleCommandSetBuyTrigger(args)

    elif args["command"] == "SET_SELL_AMOUNT":
        handleCommandSetSellAmount(args)
    elif args["command"] == "CANCEL_SELL_AMOUNT":
        handleCommandCancelSetSell(args)
    elif args["command"] == "SET_SELL_TRIGGER":
        handleCommandSetSellTrigger(args)


def handleCommandAdd(args):
    localDB.addCash(args["userId"], args["cash"])

def handleCommandBuy(args):
    print "buying..."
    symbol = args.get("sym")
    cash = args.get("cash")
    userId = args.get("userId")
    transactionNumber = args.get("lineNum")

    if localDB.getUser(userId).get("cash") >= cash:
        quote = quoteObj.getQuoteNoCache(symbol, userId, transactionNumber)

        costPer = quote.get('value')
        amount = int(cash / costPer)

        localDB.pushBuy(userId, symbol, amount, costPer)
        localDB.reserveCash(userId, amount * costPer)
    else:
        return "not enough available cash"


def handleCommandCommitBuy(args):
    print "commit buying..."
    userId = args.get("userId")
    buy = localDB.popBuy(userId)
    if buy:
        symbol = buy.get('symbol')
        number = buy.get('number')
        costPer = buy.get('costPer')
        if localDB.isBuySellActive(buy):
            localDB.addToPortfolio(userId, symbol, number)
            localDB.commitReserveCash(userId, number * costPer)
        else:
            localDB.releaseCash(userId, number * costPer)
            return "inactive"
    else:
        return "no buys"


def handleCommandCancelBuy(args):
    userId = args.get("userId")
    buy = localDB.popBuy(userId)
    if buy:
        number = buy.get('number')
        costPer = buy.get('costPer')
        localDB.releaseCash(userId, number * costPer)
    else:
        return "no buys"


def handleCommandSell(args):
    print "selling..."
    symbol = args.get("sym")
    cash = args.get("cash")
    userId = args.get("userId")

    quote = quoteObj.getQuoteNoCache(symbol, args["userId"], args.get("lineNum"))

    costPer = quote.get('value')
    amount = math.floor(cash / costPer)

    localDB.pushSell(userId, symbol, amount, costPer)


def handleCommandCommitSell(args):
    print "commiting selling..."
    userId = args.get("userId")
    sell = localDB.popSell(userId)
    if sell:
        symbol = sell.get('symbol')
        number = sell.get('number')
        costPer = sell.get('costPer')
        if localDB.isBuySellActive(sell):
            localDB.removeFromPortfolio(userId, symbol, number)
            localDB.addCash(userId, number * costPer)
        else:
            return "inactive"
    else:
        return "no sells"


def handleCommandCancelSell(args):
    userId = args.get("userId")
    sell = localDB.popSell(userId)
    if not sell:
        return "no sells"

def handleCommandSetBuyAmount(args):
    symbol = args.get("sym")
    amount = args.get("cash")
    userId = args.get("userId")

    if localDB.getUser(userId).get("cash") >= amount:
        localDB.reserveCash(userId, amount)
        localTriggers.addBuyTrigger(userId, symbol, amount)
    else:
        return "not enough available cash"


def handleCommandSetBuyTrigger(args):
    symbol = args.get("sym")
    buyAt = args.get("cash")
    userId = args.get("userId")

    success = localTriggers.setBuyActive(userId, symbol, buyAt)
    if not success:
        return "trigger doesnt exist or is at a higher value than amount reserved for it"

def handleCommandCancelSetBuy(args):
    symbol = args["sym"]
    userId = args["userId"]

    trigger = localTriggers.cancelBuyTrigger(userId, symbol)
    if trigger:
        reserved = trigger.get('cashReserved')
        localDB.releaseCash(userId, reserved)
    else:
        return "no trigger to cancel"

def handleCommandSetSellAmount(args):
    symbol = args.get("sym")
    amount = args.get("cash")
    userId = args.get("userId")

    localTriggers.addSellTrigger(userId, symbol, amount)

def handleCommandSetSellTrigger(args):
    symbol = args.get("sym")
    sellAt = args.get("cash")
    userId = args.get("userId")

    trigger = localTriggers.setSellActive(userId, symbol, sellAt)
    if trigger:
        reserve = math.floor( trigger.get('maxSellAmount') / sellAt)
        if localDB.reserveFromPortfolio(userId, symbol, reserve):
            return
        else:
            # reset the trigger to non active
            localTriggers.addSellTrigger(userId, symbol, trigger.get('maxSellAmount'))
            return "not enough available"
    return "no trigger to activate"

def handleCommandCancelSetSell(args):
    symbol = args.get("sym")
    userId = args.get("userId")

    trigger = localTriggers.cancelSellTrigger(userId, symbol)
    if trigger:
        # if its active, need to remove from reserved portfolio
        if trigger.get('active'):
            refund = math.floor( trigger.get('maxSellAmount') / trigger.get('sellAt') )
            localDB.releasePortfolioReserves(userId, symbol, refund)
        return
    return "no trigger to cancel"

def main():
    #   starting httpserver and waiting for input
    spoolUpServer()


def spoolUpServer(handlerClass=httpsRequestHandler, serverClass=httpsServer):
    socknum = 4442

    try:
        serverAddr = ('', socknum)  # our address and port
        httpd = serverClass(serverAddr, handlerClass)
    except socket.error:
        print "socket:" + str(socknum) + " busy."
        socknum = incrementSocketNum(socknum)
        serverAddr = ('', socknum)  # our address and port
        httpd = serverClass(serverAddr, handlerClass)

    socketName = httpd.socket.getsockname()
    print "serving HTTPS on", socketName[0], "port number:", socketName[1],
    print "printing addr = " + str(serverAddr)
    print "waiting for request..."
    # this idles the server waiting for requests
    httpd.serve_forever()


def incrementSocketNum(socketNum):
    # This is used to increment the socket incase ours is being used
    socketNum += 1
    return socketNum


if __name__ == '__main__':
    # Global vars
    # -----------------------
    auditServer = AuditServer()
    quoteObj = Quotes(auditServer)
    localDB = databaseServer()
    localTriggers = Triggers()

    # trigger threads
    hammerQuoteServerToSell(quoteObj)
    hammerQuoteServerToBuy(quoteObj)
    # -----------------------

    main()
    # send dumplog
    #
