# ssh keys added for each worker, as here: https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2



workingDirectoryPath="Desktop/seng462/CSC462/transactionServer/runcode"


pssh -i -h workersHostFile.txt -x "cd $workingDirectoryPath;" grep DUMP transOutput.txt
