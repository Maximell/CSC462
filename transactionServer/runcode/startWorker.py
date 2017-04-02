import os

if __name__ == '__main__':
    try:
        print "starting triggers"
        os.system("python -u mqTriggers.py > triggerOutput.txt &")
    except:
        print "trigger server failed to start"
    try:
        print "starting transaction"
        os.system("python -u transactionServer.py > transOutput.txt &")
    except:
        print "transaction server failed to start"
    try:
        print "starting database"
        os.system("python -u mqDatabaseServer.py > databaseOutput.txt &")
    except:
        print "Database Server failed to start"
