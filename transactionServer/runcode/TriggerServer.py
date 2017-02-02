import socket
from threading import Thread

# Here we want our trigger's threads
# hitting the quote server for quotes every 15sec

class hammerQuoteServerToBuy(Thread):
    def __init__(self, quoteServer):
        Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.daemon = True
        self.quote = quoteServer
        self.start()

    def run(self):
        breakVal = False
        while True:
            if localTriggers.buyTriggers != {}:
                for userId in localTriggers.buyTriggers:
                    symDict = localTriggers.buyTriggers[userId]

                    symbols = symDict.keys()
                    for sym in symbols:
                        if symDict[sym]["active"] == True:
                            buyVal = symDict[sym]["buyAt"]
                            request = sym + "," + userId + "\n"
                            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            self.socket.connect(('quoteserve.seng.uvic.ca', 4444))
                            self.socket.send(request)
                            data = self.socket.recv(1024)
                            self.socket.close()

                            vals = self.quote._quoteStringToDictionary(data)
                            if vals["value"] <= buyVal:
                                print sym
                                print "bought for:" + str(vals["value"])
                                breakVal = True
                                # logic for buying
                                args = {"sym": sym, "userId": userId, "cash": vals["value"]}
                                handleCommandBuy(args)
                                handleCommandCommitBuy(args)
                                break
                    if breakVal:
                        break
                if breakVal:
                    break

            else:
                pass


class hammerQuoteServerToSell(Thread):
    def __init__(self, quoteServer):
        Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.daemon = True
        self.quote = quoteServer
        self.start()

    def run(self):
        breakVal = False
        while True:
            if localTriggers.sellTriggers != {}:
                for userId in localTriggers.sellTriggers:
                    symDict = localTriggers.sellTriggers[userId]
                    # if symDict["active"] == True:
                    symbols = symDict.keys()
                    for sym in symbols:
                        if symDict[sym]["active"] == True:
                            sellAt = symDict[sym]["sellAt"]
                            request = sym + "," + userId + "\n"
                            self.socket.connect(('quoteserve.seng.uvic.ca', 4444))
                            self.socket.send(request)
                            data = self.socket.recv(1024)
                            self.socket.close()
                            vals = self.quote._quoteStringToDictionary(data)
                            if vals["value"] >= sellAt:
                                print sym
                                print "sold for:" + str(vals["value"])
                                breakVal = True
                                # logic for the selling
                                args = {"sym": sym, "userId": userId, "cash": vals["value"]}
                                handleCommandSell(args)
                                handleCommandCommitSell(args)
                                break
                    if breakVal:
                        break
                if breakVal:
                    break
            else:
                pass
                # print 'B'

class Triggers:
    def __init__(self):
        self.buyTriggers = {}
        self.sellTriggers = {}

    def getBuyTriggers(self):
        return self.buyTriggers

    def getSellTriggers(self):
        return self.sellTriggers

    def addBuyTrigger(self, userId, sym, cashReserved):
        if userId not in self.buyTriggers:
            self.buyTriggers[userId] = {}
        self.buyTriggers[userId][sym] = {"cashReserved": cashReserved, "active": False, "buyAt": 0}

    def addSellTrigger(self, userId, sym, maxSellAmount):
        if userId not in self.sellTriggers:
            self.sellTriggers[userId] = {}
        self.sellTriggers[userId][sym] = {"maxSellAmount": maxSellAmount, "active": False, "sellAt": 0}

    def setBuyActive(self, userId, symbol, buyAt):
        if self._triggerExists(userId, symbol, self.buyTriggers):
            print "activating buy thread"

            trigger = self.buyTriggers.get(userId).get(symbol)
            if buyAt <= trigger.get('cashReserved'):
                trigger["active"] = True
                trigger["buyAt"] = buyAt
                # start cron job
                # threadBuyHandler.addBuyThread(symbol, buyAt)
                # print "bought: " + str(bought)
                return trigger
        return 0

    def setSellActive(self, userId, symbol, sellAt):
        if self._triggerExists(userId, symbol, self.sellTriggers):
            print "activating sell thread"

            # print self.sellTriggers.get(userId)
            # print symbol
            # print self.sellTriggers.get(userId).get(symbol)

            trigger = self.sellTriggers.get(userId).get(symbol)
            if sellAt <= trigger.get('cashReserved'):
                trigger["active"] = True
                trigger["sellAt"] = sellAt
                # start cron job
                # threadSellHandler.addSellThread(symbol , sellAt)
                # print "sold: " + str(sold)
                return trigger
        return 0

    def cancelBuyTrigger(self, userId, symbol):
        if self._triggerExists(userId, symbol, self.buyTriggers):
            removedTrigger = self.buyTriggers[userId][symbol]
            del self.buyTriggers[userId][symbol]
            return removedTrigger
        return 0

    def cancelSellTrigger(self, userId, symbol):
        if self._triggerExists(userId, symbol, self.sellTriggers):
            removedTrigger = self.sellTriggers[userId][symbol]
            del self.sellTriggers[userId][symbol]
            return removedTrigger
        return 0

    def _triggerExists(self, userId, symbol, triggers):
        if triggers.get(userId):
            if triggers.get(userId).get(symbol):
                return 1
        return 0
