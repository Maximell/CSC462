#!/usr/bin/env python
import json
from rabbitMQSetups import RabbitMQReceiver
from threading import Thread
import Queue
import time


class rabbitQueue:
    def __init__(self):
        self.queue = Queue.PriorityQueue()

class consumer (Thread):
    def __init__(self , queueName):
        Thread.__init__(self)
        self.daemon = True
        self.queueName = queueName
        self.start()

    def run(self):
        print "started"
        rabbitConsumer(self.queueName)


class rabbitConsumer():
    def __init__(self , queueName):
        self.connection = RabbitMQReceiver(self.consume , queueName)

    def consume(self, ch, method, props, body):
        payload = json.loads(body)
        line = payload.get("lineNum")
        print "got payload", payload
        if line is None:
            line = payload.get("transactionNum")

        if props.priority == 1:
            # flipping priority b/c Priority works lowestest to highest
            # But our system works the other way.

            # We need to display lineNum infront of payload to so get() works properly
            rabbit.queue.put((2, [line , payload]))
        elif props.priority == 2:
            rabbit.queue.put((1, [line , payload]))
        else:
            # This is for the dumplog
            rabbit.queue.put((3, [line , payload]))

class auditFunctions:
    USER_COMMAND = 1
    QUOTE_SERVER = 2
    ACCOUNT_TRANSACTION = 3
    SYSTEM_EVENT = 4
    ERROR_MESSAGE = 5
    DEBUG_MESSAGE = 6
    WRITE_LOGS = 7

    @classmethod
    def createUserCommand(cls, timeStamp, server, transactionNum, userId, commandName, stockSymbol=None, fileName=None, amount=None):
        obj = {
            'function': cls.USER_COMMAND,
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'commandName': commandName,
        }
        if stockSymbol:
            obj['stockSymbol'] = stockSymbol
        if fileName:
            obj['fileName'] = fileName
        if amount:
            obj['amount'] = amount
        return obj

    @classmethod
    def createQuoteServer(cls, timeStamp, server, transactionNum, userId, quoteServerTime, stockSymbol, price, cryptoKey):
        return {
            'function': cls.QUOTE_SERVER,
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'quoteServerTime': quoteServerTime,
            'stockSymbol': stockSymbol,
            'price': price,
            'cryptoKey': cryptoKey
        }

    @classmethod
    def createAccountTransaction(cls, timeStamp, server, transactionNum, userId, commandName, action, funds):
        return {
            'function': cls.ACCOUNT_TRANSACTION,
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'commandName': commandName,
            'action': action,
            'funds': funds
        }

    @classmethod
    def createSystemEvent(cls, timeStamp, server, transactionNum, userId, commandName, stockSymbol=None, fileName=None, amount=None):
        return {
            'function': cls.SYSTEM_EVENT,
            'todo': "still needs to be done"
        }

    @classmethod
    def createErrorMessage(cls, timeStamp, server, transactionNum, userId, commandName, errorMessage):
        return {
            'function': cls.ERROR_MESSAGE,
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'commandName': commandName,
            'errorMessage': errorMessage
        }

    @classmethod
    def createDebugMessage(cls, timeStamp, server, transactionNum, userId, commandName, debugMessage):
        return {
            'function': cls.DEBUG_MESSAGE,
            'todo': "still needs to be done"
        }

    @classmethod
    def createWriteLogs(cls, timeStamp, server, transactionNum, userId, command):
        return {
            'function': cls.WRITE_LOGS,
            'timeStamp': timeStamp,
            'transactionNum': transactionNum,
            'userId': userId,
            'command': command
        }

    @classmethod
    def listOptions(cls):
        return [attr for attr in dir(auditFunctions) if not callable(attr) and not attr.startswith("__") and attr != "listOptions" ]


# Class for a logging 'server'
# In general, an event takes the form of:
#   event = {
#       'type': 'someType',
#           userCommand
#           accountTransaction
#           systemEvent
#           quoteServer
#           errorEvent
#       'timestamp': seconds since the epoch,
#       'server': 'where the server originated from',
#       'transactionNum': the transaction number the event is associated with,
#       'username': 'userId of the user who triggered the event'
#       'args': {} Some dictionary - specific for the type of event.
#   }
#   Valid 'type's and their arg values:
#       userCommand
#           args: {
#               'command': {'name': ,
#                           args{}}'string representing the user's command',
#                   add
#                   commit_buy
#                   cancel_buy
#                   commit_sell
#                   cancel_sell
#                   display_summary
#                       no additional args
#
#                   quote
#                   buy
#                   sell
#                   set_buy_amount
#                   cancel_set_buy
#                   set_buy_trigger
#                   set_sell_amount
#                   set_sell_trigger
#                   cancel_set_sell
#                       need stockSymbol
#
#                   dumplog
#                       fileName
#
#                   add
#                   buy
#                   sell
#                   set_buy_amount
#                   set_buy_trigger
#                   set_sell_amount
#                   set_sell_trigger
#                       funds
#           }
#       accountTransaction
#           args: {
#               'action': string corresponding to type of account transaction
#                   add
#                   remove
#                   reserve
#                   free
#               'funds': amount of money being moved
#           }
#       systemEvent
#           args: {
#               'command': same as in userCommand
#           }
#       quoteServer
#           args: {
#               'quoteServerTime': time the quote was received from the quote server,
#               'stockSymbol': 'stcksymbl',
#               'price': price of the stock at the time the server quoted it,
#               'cryptokey': 'cryptographic key the server returns'
#           }
#       errorEvent
#           args: {
#               'command': same as in userCommand,
#               'errorMessage': message associated with the error
#           }
class AuditServer:
    def __init__(self):
        self.logFile = []

    # TODO: need a logAdminCommand which doesnt have userId (for dumplog command)
    def logUserCommand(self, timeStamp, server, transactionNum, userId, commandName, stockSymbol=None, fileName=None, amount=None):
        dictionary = {
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'commandName': commandName,
            'logType': 'userCommand'
        }
        if stockSymbol:
            dictionary = dict(dictionary, stockSymbol=stockSymbol)
        if fileName:
            dictionary = dict(dictionary, fileName=fileName)
        if amount:
            dictionary = dict(dictionary, amount=amount)
        self.logFile.append(dictionary)
        return dictionary

    def logQuoteServer(self, timeStamp, server, transactionNum, userId, quoteServerTime, stockSymbol, price, cryptoKey):
        dictionary = {
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'logType': 'quoteServer',
            'quoteServerTime': quoteServerTime,
            'stockSymbol': stockSymbol,
            'price': price,
            'cryptoKey': cryptoKey
        }
        self.logFile.append(dictionary)
        return dictionary

    def logAccountTransaction(self, timeStamp, server, transactionNum, userId, commandName, action, funds):
        dictionary = {
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'commandName': commandName,
            'logType': 'accountTransaction',
            'action': action,
            'funds': funds
        }
        self.logFile.append(dictionary)
        return dictionary

    def logSystemEvent(self, timeStamp, server, transactionNum, userId, commandName, stockSymbol=None, fileName=None, amount=None):
        dictionary = {
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'commandName': commandName,
            'logType': 'systemEvent'
        }
        if stockSymbol:
            dictionary = dict(dictionary, stockSymbol=stockSymbol)
        if fileName:
            dictionary = dict(dictionary, fileName=fileName)
        if amount:
            dictionary = dict(dictionary, amount=amount)
        self.logFile.append(dictionary)
        return dictionary

    def logErrorMessage(self, timeStamp, server, transactionNum, userId, commandName, errorMessage):
        dictionary = {
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'commandName': commandName,
            'logType': 'errorEvent',
            'errorMessage': errorMessage
        }
        self.logFile.append(dictionary)
        return dictionary

    def logDebugMessage(self, timeStamp, server, transactionNum, userId, commandName, debugMessage):
        dictionary = {
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'commandName': commandName,
            'logType': 'debugEvent',
            'debugMessage': debugMessage
        }
        self.logFile.append(dictionary)
        return dictionary

    def writeLogs(self, fileName):
        self._dumpIntoFile(fileName)
        return {
            "success": True
        }

    # dumps the logs to a given file
    def _dumpIntoFile(self, fileName):
        try:
            file = open(fileName, 'w')
        except IOError:
            print 'Attempted to save into file %s but couldn\'t open file for writing.' % (fileName)

        file.write('<?xml version="1.0"?>\n')
        file.write('<log>\n\n')
        for log in self.logFile:
            logType = log['logType']
            file.write('\t<' + logType + '>\n')
            file.write('\t\t<timestamp>' + str(log['timeStamp']) + '</timestamp>\n')
            file.write('\t\t<server>' + str(log['server']) + '</server>\n')
            file.write('\t\t<transactionNum>' + str(log['transactionNum']) + '</transactionNum>\n')
            if log['userId'] != "./testLOG":
                file.write('\t\t<username>' + str(log['userId']) + '</username>\n')
            if logType == 'userCommand':
                file.write('\t\t<command>' + str(log['commandName']) + '</command>\n')
                if log.get('stockSymbol'):
                    file.write('\t\t<stockSymbol>' + str(log['stockSymbol']) + '</stockSymbol>\n')
                if log.get('fileName'):
                    file.write('\t\t<filename>' + str(log['fileName']) + '</filename>\n')
                if log.get('amount'):
                    file.write('\t\t<funds>' + str(log['amount']) + '</funds>\n')
            elif logType == 'quoteServer':
                file.write('\t\t<quoteServerTime>' + str(log['quoteServerTime']) + '</quoteServerTime>\n')
                file.write('\t\t<stockSymbol>' + str(log['stockSymbol']) + '</stockSymbol>\n')
                file.write('\t\t<price>' + str(log['price']) + '</price>\n')
                file.write('\t\t<cryptokey>' + str(log['cryptoKey']) + '</cryptokey>\n')
            elif logType == 'accountTransaction':
                file.write('\t\t<action>' + str(log['action']) + '</action>')
                file.write('\t\t<funds>' + str(log['amount']) + '</funds>')
            elif logType == 'systemEvent':
                file.write('\t\t<command>' + str(log['commandName']) + '</command>\n')
                if log.get('stockSymbol'):
                    file.write('\t\t<stockSymbol>' + str(log['stockSymbol']) + '</stockSymbol>\n')
                if log.get('fileName'):
                    file.write('\t\t<filename>' + str(log['fileName']) + '</filename>\n')
                if log.get('amount'):
                    file.write('\t\t<funds>' + str(log['amount']) + '</funds>\n')
            elif logType == 'errorEvent':
                file.write('\t\t<command>' + str(log['commandName']) + '</command>\n')
                if log.get('errorMessage'):
                    file.write('\t\t<errorMessage>' + str(log['errorMessage']) + '</errorMessage>\n')
            elif logType == 'debugMessage':
                file.write('\t\t<debugMessage>' + str(log['debugMessage']) + '</debugMessage>\n')
            file.write('\t</'+ logType +'>\n')
        file.write('\n</log>\n')
        file.close()
        print "Log file written to file: " + str(fileName)
        return "Log file written to file: " + str(fileName)

def handleUserCommand(payload):
    return auditServer.logUserCommand(
        payload["timeStamp"],
        payload["server"],
        payload["transactionNum"],
        payload["userId"],
        payload["commandName"],
        stockSymbol=payload.get("stockSymbol"),
        fileName=payload.get("fileName"),
        amount=payload.get("amount")
    )

def handleQuoteServer(payload):
    return auditServer.logQuoteServer(
        payload["timeStamp"],
        payload["server"],
        payload["transactionNum"],
        payload["userId"],
        payload["quoteServerTime"],
        payload["stockSymbol"],
        payload["price"],
        payload["cryptoKey"]
    )

def handleAccountTransaction(payload):
    return auditServer.logUserCommand(
        payload["timeStamp"],
        payload["server"],
        payload["transactionNum"],
        payload["userId"],
        payload["commandName"],
        stockSymbol=payload.get("stockSymbol"),
        fileName=payload.get("fileName"),
        amount=payload.get("amount")
    )

def handleSystemEvent(payload):
    return auditServer.logUserCommand(
        payload["timeStamp"],
        payload["server"],
        payload["transactionNum"],
        payload["userId"],
        payload["commandName"],
        stockSymbol=payload.get("stockSymbol"),
        fileName=payload.get("fileName"),
        amount=payload.get("amount")
    )

def handleErrorMessage(payload):
    auditServer.logErrorMessage(payload.get("timeStamp"), payload.get("server"), payload.get("transactionNum"),
                                payload.get("userId"), payload.get("command"), payload.get("errorMessage"))
    return "audit logging error message not implemented"

def handleDebugMessage(payload):
    return auditServer.logUserCommand(
        payload["timeStamp"],
        payload["server"],
        payload["transactionNum"],
        payload["userId"],
        payload["commandName"],
        payload["debugMessage"]
    )

def handleWriteLogs(payload):
    return auditServer.writeLogs("./testLOG")


def on_request(ch, method, props, payload):
    print "received payload", payload
    print props

    function = payload["function"]
    print "function: ", function
    try:
        handleFunctionSwitch[function](payload)
    except KeyError as error:
        print "keyError (possible function not found):", str(error)


if __name__ == '__main__':
    print "starting AuditServer"

    auditServer = AuditServer()


    handleFunctionSwitch = {
        auditFunctions.USER_COMMAND: handleUserCommand,
        auditFunctions.QUOTE_SERVER: handleQuoteServer,
        auditFunctions.ACCOUNT_TRANSACTION: handleAccountTransaction,
        auditFunctions.SYSTEM_EVENT: handleSystemEvent,
        auditFunctions.ERROR_MESSAGE: handleErrorMessage,
        auditFunctions.DEBUG_MESSAGE: handleDebugMessage,
        auditFunctions.WRITE_LOGS: handleWriteLogs
    }
    rabbit = rabbitQueue()
    consumeRabbit = consumer(RabbitMQReceiver.AUDIT)
    print rabbit.queue

    seenDumpLog = False
    countDown = 0
    DumpLog = None
    DumpLogProps = None

    while (True):
        # check if queue is empty
        if rabbit.queue.empty():
            # print "empty"
            if seenDumpLog:
                time.sleep(1)
                countDown += 1
                # send dumplog if you haven't seen anything for 30 sec
                if countDown == 60:
                    print "Making Dumplog"
                    on_request(None, None, DumpLogProps, DumpLog)


            continue
        # else service queue
        else:
            countDown = 0
            msg = rabbit.queue.get()
            payload = msg[1]
            args = payload[1]
            props = msg[0]
            print "queue size: ", rabbit.queue.qsize()
            if args.get("command") == "DUMPLOG":
                print "seen Dumplog"
                seenDumpLog = True
                DumpLog = args
                DumpLogProps = props

            else:
                on_request(None, None, props, args)

# auditServer.writeLogs("./testLOG")