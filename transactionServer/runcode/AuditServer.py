# library imports
import requests
from flask import Flask

from OpenSSL import SSL
context = SSL.Context(SSL.SSLv23_METHOD)
# server.pem's location (containing the server private key and the server certificate).
# fpem = "cert.pem"
# context.use_privatekey_file(fpem)
# context.use_certificate_file(fpem)
context = ('key.key' , 'cert1.crt')

app = Flask(__name__)

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

    '''
#   TO BE IMPLEMENTED WHEN WE MOVE TO EVENTS
    def log(self, event):
        print 'Logging an event: ' + event + '.'
        self.logFile.append(event)
    '''

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

    # def logUserCommand(self, **kwargs):
    #     self.logFile.append(dict(kwargs,
    #                              logType='userCommand'
    #                              ))

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
        print "Log file written."


    # # Call Quote
    # if "./testLOG" != args["userId"]:
    #     # TODO: not sure how filename comes in
    #     auditServer.logUserCommand(
    #         int(time.time() * 1000),
    #         "transaction",
    #         args.get('lineNum'),
    #         args.get('userId'),
    #         args.get("command"),
    #         stockSymbol=args.get('sym'),
    #         fileName=None,
    #         amount=args.get('cash')
    #     )
    #     localDB.addUser(args["userId"])
    # else:
    #     # TODO: not sure how filename comes in
    #     fileName = args.get('userId')
    #     auditServer.logUserCommand(
    #         int(time.time() * 1000),
    #         "transaction",
    #         args.get('lineNum'),
    #         "TODO get user properly",
    #         args.get("command"),
    #         stockSymbol=args.get('sym'),
    #         fileName=fileName,
    #         amount=args.get('cash')
    #     )
    #     auditServer.writeLogs(fileName)


@app.route('/')
def index():
    return 'FlaskAuditServer is running!'

# User Command Log
@app.route('/add/<float:timeStamp>/<string:server>/<int:lineNum>/<string:userId>/<string:userId>/<string:command>/<string:sym>/<string:fileName>/<float:cash>', methods=['POST'])
@app.route('/add/<float:timeStamp>/<string:server>/<int:lineNum>/<string:userId>/<string:userId>/<string:command>/<string:sym>/<string:fileName>/<int:cash>', methods=['POST'])
def LogUserCommand(timeStamp, server, transactionNum, userId, commandName, stockSymbol=None, fileName=None, cash=None):
    return "Log user Command" % auditServer.logUserCommand(timeStamp, server, transactionNum, userId, commandName, stockSymbol, fileName, cash)

# Quote Server Log
@app.route('/add/<float:timeStamp>/<string:server>/<int:lineNum>/<string:userId>/<string:userId>/<string:command>/<string:sym>/<string:fileName>/<float:cash>', methods=['POST'])
@app.route('/add/<float:timeStamp>/<string:server>/<int:lineNum>/<string:userId>/<string:userId>/<string:command>/<string:sym>/<string:fileName>/<int:cash>', methods=['POST'])
def LogQuoteServer(timeStamp, server, transactionNum, userId, commandName, stockSymbol=None, fileName=None, cash=None):
    return "Quote Server" % auditServer.logQuoteServer(timeStamp, server, transactionNum, userId, commandName, stockSymbol, fileName, cash)

# Account Transaction Log
@app.route('/add/<float:timeStamp>/<string:server>/<int:lineNum>/<string:userId>/<string:userId>/<string:command>/<string:action>/<string:fileName>/<float:funds>', methods=['POST'])
@app.route('/add/<float:timeStamp>/<string:server>/<int:lineNum>/<string:userId>/<string:userId>/<string:command>/<string:action>/<string:fileName>/<int:funds>', methods=['POST'])
def LogAccountTransaction(timeStamp, server, transactionNum, userId, commandName, action, funds):
    return "Log Account Transaction" % auditServer.logAccountTransaction(timeStamp, server, transactionNum, userId, commandName, action, funds)

# System event log
@app.route('/add/<float:timeStamp>/<string:server>/<int:lineNum>/<string:userId>/<string:userId>/<string:command>/<string:sym>/<string:fileName>/<float:cash>', methods=['POST'])
@app.route('/add/<float:timeStamp>/<string:server>/<int:lineNum>/<string:userId>/<string:userId>/<string:command>/<string:sym>/<string:fileName>/<int:cash>', methods=['POST'])
def LogSystemEvent(timeStamp, server, transactionNum, userId, commandName, stockSymbol=None, fileName=None, cash=None):
    return "System event logged" % auditServer.logSystemEvent(timeStamp, server, transactionNum, userId, commandName, stockSymbol, fileName, cash)

# Error msg log
@app.route('/add/<float:timeStamp>/<string:server>/<int:lineNum>/<string:userId>/<string:userId>/<string:command>/<string:error>, methods=['POST'])
def LogErrorMessage(timeStamp, server, transactionNum, userId, commandName, error):
    return "error msg logged" % auditServer.logErrorMessage(timeStamp, server, transactionNum, userId, commandName, error)
# Debug msg log
@app.route('/add/<float:timeStamp>/<string:server>/<int:lineNum>/<string:userId>/<string:userId>/<string:command>/<string:debugMsg>/<string:fileName>/<float:cash>',methods=['POST'])
def LogDebugMessage(timeStamp, server, transactionNum, userId, commandName, debugMsg):
    return "Logging Debugg msg" % auditServer.logDebugMessage(timeStamp, server, transactionNum, userId, commandName, debugMsg)
# Dumplog
@app.route('/dumplog/<string:fileName>')
def DumpIntoFile(fileName=None):
    return "Dumplog" % auditServer._dumpIntoFile( fileName)



if __name__== '__main__':
    auditServer = AuditServer()
    app.run(host='127.0.0.2', debug=True, ssl_context=context)

