# ssh keys added for each worker, as here: https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2
# you need your own keykey to run this script across other machines. Follow ^ these instructions.


# this command needs to be run from machine 142, as that is where the private-key is held.
# this script is for starting up all the vms.

# there are 4 'types' of servers:
#   test driver (run on 142)
#   'workers' that contain a transactionserver, triggerserver, and db
#   audit server (also runs on 142)
#   quote server (also runs on 142

echo This should be run ./manageVMsUP.sh username
echo
echo This work is been done on $1
echo This script should be run on the LAB COMPUTER b142
echo This is not to be run on the VM

startvm () {
    echo doing configuration for :
    hostname
    echo List all VMs:
    vbm=($(VBoxManage list runningvms))
    echo ${vbm[0]}
    if  test -n ${vbm[0]} ; then
        echo VM already on
    else
        echo Start seng462scratch
        #VBoxManage startvm seng462scratch --type headless
    fi
}

# Doing the configuration for the local machine
startvm
host=$1

#Doing the configuration for other machines.
for ip in 'computerIPS.txt'; do
  login=$host$ip
  ssh $login -t -t "$(typeset -f);startvm"
  echo $login



#




#VBoxManage controlvm <vm> acpipowerbutton
