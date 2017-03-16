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
echo sleeping for 5 seconds so RMQmanager has time to boot
sleep 5
echo starting host servers
python startHostServers.py

echo finished local configuration

# Do the configuration on the worker machines
echo attempting to configure workers
echo assigning the working directory path to a variable
workingDirectoryPath="Desktop/seng462/CSC462/transactionServer/runcode"

echo getting latest code
pssh -i -h workersHostFile.txt -x "cd $workingDirectoryPath" git pull
echo killing all python
pssh -i -h workersHostFile.txt killall python
echo starting workers
pssh -i -h workersHostFile.txt -x "cd $workingDirectoryPath" python runScript.py
echo worker configuration complete

#waiting to make sure everything has started
echo waiting for 5 seconds to make sure everything has started
sleep 5
echo done waiting

if [ $1 ]; then
    python runWorkload.py $1
else
    echo This script must be run with the workload file as a parameter
fi