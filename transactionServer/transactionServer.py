
# demonstrate talking to the quote server
import socket, sys
from OpenSSL import SSL
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from SocketServer import BaseServer
import pprint


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

# Dictionary for users and database
dict = {}
cache = {}


class httpsServer(HTTPServer):
    def __init__(self, serverAddr, handlerClass ):
        BaseServer.__init__(self, serverAddr, handlerClass)
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        # server.pem's location (containing the server private key and
        # the server certificate).
        # fpem = "pathToCert\cert.pem"
        # ctx.use_privatekey_file(fpem)
        # ctx.use_certificate_file(fpem)
        self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
                                                        self.socket_type))
        self.server_bind()
        self.server_activate()

class httpsRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self):
        self.connection = self.request
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)
        self.rfile = socket._fileobject(self.request, "rb", self.wbufsize)


def main():
      spoolUpServer()
#     httpserver waiting for input
#     once we have input figure out what it is.


      # once we have userID check to see if in the dict
      checkUser(userID)

      # depending on what happens hit the quote server
      doCommand()

def spoolUpServer(handlerClass = httpsRequestHandler,serverClass = httpsServer):
    print "test"
    serverAddr = ('' , 443) #our address and port
    httpd = serverClass(serverAddr, handlerClass)
    socketName = httpd.socket.getsockname()
    print "serving HTTPS on" , socketName[0], "port number:", socketName[1],
    print "waiting for request..."
    httpd.serve_forever()


def checkUser(userID):
    # adding user to DB
    # NOTE (usersnames need newline char to activate quoteserver)
    if userID not in dict:
        dict[userID] = 0
        print "adding user"

def doCommand():
    # if quote hit the quote server and add sym to cache
    # if cmd == quote:
        if sym not in cache:
            data = quote(str(sym+userID+"\n"))
        #     add data to cache
        #     this data is good for 60sec
        else:
            return cache[sym]

    # currently just send a quote for "abc" for user steave.

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
    quote(s, fromUser)
    s.send(fromUser)
    data = s.recv(1024)
    print data
    # close the connection, and the socket
    s.close()

def quote(socket , input):
    socket.send(input)
    data = s.recv(1024)
    print "sending quote"
    return  data





if __name__ == '__main__':
    main()