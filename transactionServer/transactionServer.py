
# demonstrate talking to the quote server
import socket, sys
import ssl
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from SocketServer import BaseServer


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


def main():
#     httpserver waiting for input
#     once we have input figure out what it is.
      userID = "steave"
      checkUser(userID)

      # depending on what happens hit the quote server
      sendCommandToQS()

def checkUser(userID):
    # adding user to DB
    # NOTE (usersnames need newline char to activate quoteserver)
    if userID not in dict:
        dict[userID] = 0
        print "adding user"

def sendCommandToQS():
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
    print "sending quote"





if __name__ == '__main__':
    main()