# This script is just to start the servers
# This script should be inside the transactionsServer/runcode dir
# Right now the host computer will be B142.

import os
import sys

if __name__ == '__main__':
    # start quote server
    try:
        os.system("python -u mqQuoteServer.py > quoteOutput.txt &")
    except:
        print "quote server failed to start"
