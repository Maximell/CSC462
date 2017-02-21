#!/usr/bin/env python
import pika
import time
import json
import queueNames
import math
import ast

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
            'todo': "still needs to be done"
        }

    @classmethod
    def createDebugMessage(cls, timeStamp, server, transactionNum, userId, commandName, debugMessage):
        return {
            'function': cls.DEBUG_MESSAGE,
            'todo': "still needs to be done"
        }

    @classmethod
    def listOptions(cls):
        return [attr for attr in dir(auditFunctions) if not callable(attr) and not attr.startswith("__") and attr != "listOptions" ]

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

    def logAccountTransaction(self, timeStamp, server, transactionNum, userId, commandName, action, funds):
        dictionary = {
            'timeStamp': timeStamp,
            'server': server,
            'transactionNum': transactionNum,
            'userId': userId,
            'logType': 'accountTransaction',
            'action': action,
            'funds': funds
        }
        self.logFile.append(dictionary)

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

    def writeLogs(self, fileName):
        self._dumpIntoFile(fileName)

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
            elif logType == 'errorMessage':
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
    return auditServer.logUserCommand(
        payload["timeStamp"],
        payload["server"],
        payload["transactionNum"],
        payload["userId"],
        payload["commandName"],
        payload["errorMessage"]
    )

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
    return auditServer.writeLogs(payload["fileName"])

def on_request(ch, method, props, body):
    payload = json.loads(body)
    function = payload["function"]
    args = ast.literal_eval(body)

    try:
        response = handleFunctionSwitch[function](payload)
    except KeyError:
        response = create_response(404, "function not found")

    response = json.dumps(response)

    ch.basic_publish(
        exchange='',
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body=response
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
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

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queueNames.AUDIT)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_request, queue=queueNames.AUDIT)

    print("awaiting audit requests")
    channel.start_consuming()
