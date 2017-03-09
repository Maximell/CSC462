# This script is just to a test to start the servers
# This script should be inside the transactionsServer/runcode dir
import os
import sys

if __name__ == '__main__':
    # start transaction server
    try:
        os.system("python -u mqAuditServer.py > auditOutput.txt &")
    except:
        print "Audit server failed to start"
    try:
        os.system("python -u mqQuoteServer.py > quoteOutput.txt &")
    except:
        print "quote server failed to start"



    #os.system("killall python")
