import os
import sys

if __name__ == '__main__':
    # start audit server
    try:
        os.system("python -u mqAuditServer.py > auditOutput.txt &")
    except:
        print "Audit server failed to start"
