# This script is just to a test to start the servers
# This script should be inside the transactionsServer/runcode dir
import os
import sys
import time

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('INCORRECT PARAMETERS FOR TESTDRIVER\n')
        print('example: python3 testDriver.py http://localhost:8000 2userWorkLoad.txt')
    # start the webserver
    try:
        # os.system("gunicorn --workers 10 --bind 127.0.0.1:5000 wsgi > webserverOutput.txt &")
        os.system("python -u webServer.py > webserverOutput.txt &")
    except:
        print "quote server failed to start"
    # start transaction server
    try:
        os.system("python -u mqAuditServer.py > auditOutput.txt &")
    except:
        print "Audit server failed to start"
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
    # start Quote server
    try:
        os.system("python -u mqQuoteServer.py > quoteOutput.txt &")
    except:
        print "quote server failed to start"
    print "waiting before running the test driver"
    time.sleep(5);
    print "starting the test driver"
    # start the testDriver
    try:
        os.system("python3.5 ../../testDriver/runcode/testDriver.py http://127.0.0.1:5000 " + str(sys.argv[1]))
    except:
        print "test driver failed to start"
    #os.system("killall python")
