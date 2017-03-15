# ssh keys added for each worker, as here: https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2

# this command needs to be run from machine 142, as that is where the private-key is held.

# there are 4 'types' of servers:
#   test driver (run on 142)
#   'workers' that contain a transactionserver, triggerserver, and db
#   audit server (also runs on 142)
#   quote server (also runs on 142

# Do the configuration on the local machine
echo doing local configuration
echo this script should be run in the runcode folder of the project
echo getting latest code
git pull
echo killing current python processes
killall python
echo killing RMQmanager
docker kill RMQmanager
echo starting RMQmanager
docker start RMQmanager
echo starting host servers
./startHostServers.py

echo finished local configuration

# Do the configuration on the worker machines
echo attempting to configure workers
pssh -h workersHostFile.txt cd Desktop/seng462/CSC462/transactionServer/runcode
echo getting latest code
pssh -h workersHostFile.txt git pull
echo killing all python
pssh -h workersHostFile.txt killall python
echo starting workers
pssh -h workersHostFile.txt ./runScript.py
echo worker configuration complete

#waiting to make sure everything has started
echo waiting for 5 seconds to make sure everything has started
sleep 5
echo done waiting

if $1 then
    #start the testDriver
    ./runWorkload $1
else
    echo This script must be run with the workload file as a parameter
fi