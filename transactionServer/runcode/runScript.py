# This script is just to a test to start the servers
# This script should be inside the transactionsServer/runcode dir
import os
import sys

if __name__ == '__main__':
    # start transaction server
    # start Webserver
    try:
        os.system("python -u webServer.py > webserverOutput.txt &")
    except:
        print "quote server failed to start"
    try:
        os.system("python -u mqTriggers.py > triggerOutput.txt &")
    except:
        print "Audit server failed to start"
    try:
        os.system("python -u transactionServer.py > transOutput.txt &")
    except:
        print "transaction server failed to start"
    # start database
    try:
        os.system("python -u mqDatabaseServer.py > databaseOutput.txt &")
    except:
        print "Database Server failed to start"

    try:
        os.system("python3.5 ../../testDriver/runcode/testDriver.py http://127.0.0.1:5000 " + str(sys.argv[1]))
    except:
        print "test driver failed to start"
    #os.system("killall python")
