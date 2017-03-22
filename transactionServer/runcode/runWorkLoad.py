# This is file is so we can run our testdriver from a seperate computer other than the host.
# Right now this is to be run on b131
#
import os
import sys


try:
    os.system("python ../../testDriver/runcode/rabbitTestDriver.py " + str(sys.argv[1]))
except Exception as e:
    print e
    print "test driver failed to start"