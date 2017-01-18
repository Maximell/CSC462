# pip3.6 install requests
import requests
import asyncio
import sys

def send(command, args, lineNum):
	r = requests.post(base_url, data = {'command': command, 'args': args, 'lineNum': lineNum})
	print(r.status_code)

async def sendRequests(userCommandList):
	for command in userCommandList:
	    	send(command['command'], command['args'], command['lineNum'])

def splitUsersFromFile():
	userActions = {}
	with open(sys.argv[2]) as f:
	    for line in f:
	    	splitLine = line.split(" ")
	    	lineNumber = splitLine[0]

	    	commandAndArgs = splitLine[1].split(",")

	    	command = commandAndArgs[0]
	    	args = commandAndArgs[1:]

	    	username = args[0]
	    	if not username.startswith("./"):
		    	if username not in userActions.keys():
		    		userActions[username] = []
	    		userActions[username].append({'command': command, 'args': args, 'lineNum': lineNumber})

	return userActions

async def main():
	userActions = splitUsersFromFile()
	for userSpecificActions in userActions:
		asyncio.ensure_future( sendRequests( userActions[userSpecificActions] ) )


if __name__ == '__main__':
	if len(sys.argv) < 3:
		print("\033[1;31;40mINCORRECT PARAMETERS\n")
		print("\033[1;32;40mpython3 testDriver.py <url> <file>")
		print("example: python3 testDriver.py http://localhost:8000 2userWorkLoad.txt")
		print("\033[0;37;40m")
	else:
		base_url = sys.argv[1]
		loop = asyncio.get_event_loop()
		loop.run_until_complete(main())
		loop.close()
		
