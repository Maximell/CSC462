# ssh keys added for each worker, as here: https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2
# you need your own keykey to run this script across other machines. Follow ^ these instructions.


# this command needs to be run from machine 142, as that is where the private-key is held.
# this script is for starting up all the vms.

# there are 4 'types' of servers:
#   test driver (run on 142)
#   'workers' that contain a transactionserver, triggerserver, and db
#   audit server (also runs on 142)
#   quote server (also runs on 142

echo This work is been done on $1
echo This script should be run on the LAB COMPUTER b142
echo This is not to be run on the VM

shutdownVMs () {
    echo "doing configuration for:"
    hostname
    echo List all runningvms:
    vbm=($(VBoxManage list runningvms))
    echo ${vbm[0]}

    echo "shutting down vm"
    VBoxManage controlvm 'seng462scratch' acpipowerbutton

}

host=$1

#Doing the configuration for other machines.
while read p; do
  login=$host$p
  echo $login
  ssh $login -n -t -t "$(typeset -f);shutdownVMs"
done <computerIPS.txt


# Doing the configuration for the local machine
echo "Doing Local Shutdown of 142:"
shutdownVMs



