CSC462

This readme should include:
- how to deploy
  - commands
  - server names
  - credentials

Notes

How to connect to lab machines.
- ssh netlinkID@B142.seng.uvic.ca

Things you need on your local machine to run the deploy script:
- ssh
- sudo apt-get install expect

HOW TO DEPLOY
- on machine b142
- go to group2 scratch folder
- $VBoxManage startvm seng462scratch
- ssh -p 3022 root@127.0.0.1
- enter password: seng462
- /Desktop/seng462/
- start transaction server
- cd transactionServer
- docker build -t server .
- cd testDriver
- docker build -t testdriver .
- open another terminal
- iptables -t nat -L
- in transactionServer
- docker run -p 0.0.0.0::4442 server
- in testDriver
- docker run testdriver 
