# ssh keys added for each worker, as here: https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2

# this command needs to be run from machine 142, as that is where the private-key is held.
# this script is for starting up all the vms.

# there are 4 'types' of servers:
#   test driver (run on 142)
#   'workers' that contain a transactionserver, triggerserver, and db
#   audit server (also runs on 142)
#   quote server (also runs on 142

echo this should be run ./manageVMsUP.sh
echo
echo This script should be run on the LAB COMPUTER b142
echo This is not to be run on the VM

# Doing the configuration for the local machine
echo doing local configuration
echo List all VMs:
vbm=($(VBoxManage list runningvms))
echo ${vbm[0]}
if vbm[0]; then
    echo VM already on
else;
    echo Start seng462scratch
#VBoxManage list vms


#VBoxManage startvm seng462scratch --type headless
#VBoxManage controlvm <vm> acpipowerbutton
