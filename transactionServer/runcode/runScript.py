# This script is just to a test to start the servers
# This script should be inside the transactionsServer/runcode dir
import os
import sys

if __name__ == '__main__':
    # start a 'worker' module, which includes:
    #   transactionServer
    #   triggerServer
    #   databaseServer
    # try:
    #     os.system("python -u webServer.py > webserverOutput.txt &")
    # except:
    #     print "web server failed to start"
    try:
        os.system("python -u mqTriggers.py > triggerOutput.txt &")
    except:
        print "trigger server failed to start"
    try:
        os.system("python -u transactionServer.py > transOutput.txt &")
    except:
        print "transaction server failed to start"
    try:
        os.system("python -u mqDatabaseServer.py > databaseOutput.txt &")
    except:
        print "Database Server failed to start"
