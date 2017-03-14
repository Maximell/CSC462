# This is file is so we can run our testdriver from a seperate computer other than the host.
# Right now this is to be run on b131
#
import os


try:
    os.system("python3.5 ../../testDriver/runcode/testDriver.py " + str(sys.argv[1]))
except:
    print "test driver failed to start"