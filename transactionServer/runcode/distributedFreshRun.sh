# ssh keys added for each worker, as here: https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2

# this command needs to be run from machine 142, as that is where the private-key is held.

# there are 4 'types' of servers:
#   test driver (run on 142)
#   'workers' that contain a transactionserver, triggerserver, and db
#   audit server (also runs on 142)
#   quote server (also runs on 142

# Do the configuration on the local machine
git pull

# Do the configuration on the worker machines
pssh -h workersHostFile.txt ls