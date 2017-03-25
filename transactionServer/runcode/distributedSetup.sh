# ssh keys added for each worker, as here: https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2

# this command needs to be run from machine 142, as that is where the private-key is held.
# quote server is running from root@142.104.91.130:44421
# Audit server and testdriver are on root@142.104.91.131:44421
# there are 4 'types' of servers:
#   test driver (run on 142)
#   'workers' that contain a transactionserver, triggerserver, and db
#   audit server (also runs on 142)
#   quote server (also runs on 142

echo this should be run ./distributedSetup.sh branch

# Do the configuration on the local machine
echo doing local configuration
echo this script should be run in the runcode folder of the project
echo switching branches to $1
git checkout $1
echo getting latest code
git pull
echo killing current python processes
killall python
echo killing RMQmanager
docker kill RMQmanager
echo starting RMQmanager
docker start RMQmanager
echo sleeping for 10 seconds so RMQmanager has time to boot
echo b142 is our host for the RMQ docker
sleep 10

echo finished local configuration

echo assigning the working directory path to a variable
workingDirectoryPath="Desktop/seng462/CSC462/transactionServer/runcode"
gitpath="Desktop/seng462/CSC462/"
echo reset branch
pssh -i -h workersHostFile.txt -x "cd $gitpath;" git reset --hard
pssh -i -H root@142.104.91.130:44421 -x "cd $gitpath;" git reset --hard
pssh -i -H root@142.104.91.131:44421 -x "cd $gitpath;" git reset --hard
pssh -i -H root@142.104.91.143:44421 -x "cd $gitpath;" git reset --hard

echo deleteing runcode folders
pssh -i -h workersHostFile.txt -x "cd $workingDirectoryPath;" rm -rf ../runcode
pssh -i -H root@142.104.91.130:44421 -x "cd $workingDirectoryPath;" rm -rf ../runcode
pssh -i -H root@142.104.91.131:44421 -x "cd $workingDirectoryPath;" rm -rf ../runcode
pssh -i -H root@142.104.91.143:44421 -x "cd $workingDirectoryPath;" rm -rf ../runcode

echo fetching
pssh -i -h workersHostFile.txt -x "cd $gitpath;" git fetch
pssh -i -H root@142.104.91.130:44421 -x "cd $gitpath;" git fetch
pssh -i -H root@142.104.91.131:44421 -x "cd $gitpath;" git fetch
pssh -i -H root@142.104.91.143:44421 -x "cd $gitpath;" git fetch

# Do the configuration on the worker machines
echo attempting to configure workers
echo switching branches to $1
pssh -i -h workersHostFile.txt -x "cd $gitpath;" git checkout $1
pssh -i -H root@142.104.91.130:44421 -x "cd $gitpath;" git checkout $1
pssh -i -H root@142.104.91.131:44421 -x "cd $gitpath;" git checkout $1
pssh -i -H root@142.104.91.143:44421 -x "cd $gitpath;" git checkout $1

echo getting latest code
pssh -i -h workersHostFile.txt -x "cd $gitpath;" git pull
pssh -i -H root@142.104.91.130:44421 -x "cd $gitpath;" git pull
pssh -i -H root@142.104.91.131:44421 -x "cd $gitpath;" git pull
pssh -i -H root@142.104.91.143:44421 -x "cd $gitpath;" git pull

echo killing all python
pssh -i -h workersHostFile.txt killall python
pssh -i -H root@142.104.91.130:44421 killall python
pssh -i -H root@142.104.91.131:44421 killall python
pssh -i -H root@142.104.91.143:44421 killall python


echo configuring iptables
pssh -i -h workersHostFile.txt iptables -I INPUT -p tcp --dport 44424 -j ACCEPT

echo reset branch again
pssh -i -h workersHostFile.txt -x "cd $gitpath;" git reset --hard
pssh -i -H root@142.104.91.130:44421 -x "cd $gitpath;" git reset --hard
pssh -i -H root@142.104.91.131:44421 -x "cd $gitpath;" git reset --hard
pssh -i -H root@142.104.91.143:44421 -x "cd $gitpath;" git reset --hard

echo done configuring iptables
echo starting workers
pssh -i -h workersHostFile.txt -x "cd $workingDirectoryPath;" python runScript.py
echo worker configuration complete

echo starting quote server
pssh -i -H root@142.104.91.130:44421 -x "cd $workingDirectoryPath;" python startQuoteServer.py
echo done starting quote

echo starting audit server on b131:
pssh -i -H root@142.104.91.131:44421 -x "cd $workingDirectoryPath;" python startAuditServer.py
echo audit server started

echo waiting for 10 seconds to make sure everything has started
sleep 10
echo done waiting