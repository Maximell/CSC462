import os
import sys

if __name__ == '__main__':
    # start quoteserver 
    try:
        os.system("python -u mqQuoteServer.py > quoteOutput.txt &")
    except:
        print "quote server failed to start"

