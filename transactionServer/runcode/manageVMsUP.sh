# ssh keys added for each worker, as here: https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2
# you need your own keykey to run this script across other machines. Follow ^ these instructions.


# this command needs to be run from machine 142, as that is where the private-key is held.
# this script is for starting up all the vms.

# there are 4 'types' of servers:
#   test driver (run on 142)
#   'workers' that contain a transactionserver, triggerserver, and db
#   audit server (also runs on 142)
#   quote server (also runs on 142

echo This work is been done by $1
echo This script should be run on the LAB COMPUTER b142
echo This is not to be run on the VM

startvm () {
    echo doing configuration for :
    echo hostname:
    hostname
    vbm=($(VBoxManage list vms))
    echo All vms:
    echo ${vbm[0]}
    echo List all RunningVMs:
    vbm=($(VBoxManage list runningvms))
    echo ${vbm[0]}
    if ['seng462scratch' -eq ${vbm[0]}] ; then
        echo VM already on
    else
        echo "turning vm on"
        VBoxManage startvm 'seng462scratch' --type headless

    vbm=($(VBoxManage list runningvms))
    echo ${vbm[0]}
    fi

}

# Doing the configuration for the local machine
startvm

host=$1

#Doing the configuration for other machines.
while read p; do
  login=$host$p
  echo $login
  ssh $login -n -t -t "$(typeset -f);startvm"
done <computerIPS.txt
