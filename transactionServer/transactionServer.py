
# demonstrate talking to the quote server
import socket, sys
from OpenSSL import SSL
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from SocketServer import BaseServer
import os
import pprint
import time


# COMMANDS NEEDED
#
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
#
# dumplog    (x2)
# display_summary
#

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
#               'command': 'string representing the user's command',
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
class loggerServer:

    def __init__(self):
        self.logFile = []

    def log(action):
        print 'Logging an action: ' + action + '.'

    def logUserCommand():
    def logQuoteServerHit():
    def logAccountChange():
    def logSystemEvent():
    def logErrorMessage():
    def logDebugMessage(server, timestamp, transactionNum, command, userId, stockSymbol, fileName, funds, debugMessage):

    def writeLogs(fileName):
        print 'trying to print contents to file: %s.' % (fileName)

    # writes a single line to the log file
    def _writeLineToLogFile(line):
        self.logFile.append(line)
        return

    # writes a list of lines to the log file
    def _writeLinesToLogFile(lines):
        self.logFile.extend(lines)
        return

    # dumps the logs to a given file
    def _dumpIntoFile(fileName):
        try:
            file = open(fileName, 'w')
        except IOError:
            print 'Attempted to save into file %s but couldn\'t open file for writing.' % (fileName)
        for line in self.logFile:
            file.write(line)
        file.close()


# Class for users and database
# Users are stored:
#   {
#       userId: 'abc123',
#       cash: 0,
#       reserve: 0
#   }
class databaseServer:

    def __init__(self):
        self.database = {}

    # returns user object for success
    # returns None for user not existing
    def getUser(self, userId):
        return self.database.get(userId)

    # returns user object for success
    # returns None for failure
    def addUser(self, userId):
        user = { 'userId': userId, 'cash': 0, 'reserve': 0 }
        self.database[userId] = user
        return self.database.get(userId)

    # returns user object for success
    # returns None for failure
    def addCash(self, userId, amount):
        user = self.database.get(userId)
        if user:
            user['cash'] = user.get('cash') + amount
        else:
            user = { 'userId': userId, 'cash': amount, 'reserve': 0 }
        self.database[userId] = user
        return self.database.get(userId)

    # returns user object for success
    # returns None for failure
    def reserveCash(self, userId, amount):
        user = self.database.get(userId)
        if not user:
            return 0
        if amount > user.get('cash'):
            return 0
        else:
            user['cash'] = user.get('cash') - amount
            user['reserve'] = amount
            self.database[userId] = user
            return self.database.get(userId)

    # returns user object for success
    # returns None for failure
    def releaseCash(self, userId, amount):
        user = self.database.get(userId)
        if not user:
            return 0
        if amount > user.get('reserve'):
            return 0
        else:
            user['reserve'] = user.get('reserve') - amount
            user['cash'] = user.get('cash') + amount
            self.database[userId] = user
            return self.database.get(userId)


# quote shape: symbol: {value: string, retrieved: epoch time, user: string}
class quotes():
    def __init__(self, cacheExpire = 60):
        self.cacheExpire = cacheExpire
        self.quoteCache = {}

    def getQuote(self, symbol, user):
        cache = self.quoteCache.get(symbol)
        if cache:
            if self._cacheIsActive(cache):
                return cache
            else:
                return self._hitQuoteServerAndCache(symbol, user)

        return self._hitQuoteServerAndCache(symbol, user)

    def _hitQuoteServerAndCache(self, symbol, user):
        # Create the socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket
        s.connect(('quoteserve.seng.uvic.ca', 4442))

        request = symbol + user + "\n"
        socket.send(request)
        data = socket.recv(1024)

        s.close()

        newQuote = self._quoteStringToDictionary(data)
        self.quoteCache[symbol] = newQuote
        return newQuote

    def _quoteStringToDictionary(self, quoteString):
        # "quote, sym, userid, timestamp, cryptokey\n"
        split = quoteString.split(",")
        return {'value': split[0], 'retrieved': split[3], 'user': split[2]}

    def _cacheIsActive(self, quote):
        return (quote.get('retreived', 0) + self.cacheExpire) > int(time.time())








class httpsServer(HTTPServer):
    def __init__(self, serverAddr, handlerClass ):
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

class httpsRequestHandler(SimpleHTTPRequestHandler):
    def setup(self):
        self.connection = self.request
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)
        self.rfile = socket._fileobject(self.request, "rb", self.wbufsize)
    def do_GET(self):
        print self.command
    def do_POST(self):
        if self.request != None:
            print self.command
            print self.request
            self.send_response(200)
            doCommand()
        else:
            self.send_response(403)

        # print self.rfile
        # self.send_response("gott yea")




def main():
#   starting httpserver and waiting for input
    spoolUpServer()
#     once we have input figure out what it is.

      # once we have userID check to see if in the dict
      # checkUser(userID)

      # depending on what happens hit the quote server
    # doCommand()

def spoolUpServer(handlerClass = httpsRequestHandler, serverClass = httpsServer):
    serverAddr = ('' , 4442) #our address and port
    httpd = serverClass(serverAddr, handlerClass)
    socketName = httpd.socket.getsockname()
    # print "type: " + type(httpd)
    print "serving HTTPS on" , socketName[0], "port number:", socketName[1],
    print "waiting for request..."
    # this idles the server waiting for requests
    httpd.serve_forever()


def checkUser(userID):
    # adding user to DB
    # NOTE (usersnames need newline char to activate quoteserver)
    if userID not in dict:
        dict[userID] = 0
        print "adding user"

def doCommand():
    # if quote hit the quote server and add sym to cache

    sym = "abc , "
    userID = "steave\n"

    # Print info for the user
    print("\nEnter: StockSYM , userid");
    print("  Invalid entry will return 'NA' for userid.");
    print("  Returns: quote,sym,userid,timestamp,cryptokey\n");
    # Get a line of text from the user
    # fromUser = sys.stdin.readline();
    fromUser = sym + userID
    print fromUser


    # Create the socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect the socket
    s.connect(('quoteserve.seng.uvic.ca', 4442))
    # Send the user's query
    # s.send(fromUser)

    # Read and print up to 1k of data.
    data =  quote(s, fromUser)
    print data
    # close the connection, and the socket
    s.close()

def quote(socket , input):
    socket.send(input)
    data = socket.recv(1024)
    print "sending quote"
    return  data





if __name__ == '__main__':
    main()