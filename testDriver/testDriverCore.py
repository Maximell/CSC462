import httplib, urllib
import sys

def send(command, args, lineNum):
	print args
	params = urllib.urlencode({'params': args})
	headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
	conn = httplib.HTTPConnection(url, port)
	conn.request("POST", "/", params, headers)
	response = conn.getresponse()
	print response.status, response.reason

def sendRequests(userCommandList):
	for command in userCommandList:
	    	send(command['command'], command['args'], command['lineNum'])

def splitUsersFromFile():
	userActions = {}
	with open(sys.argv[3]) as f:
	    for line in f:
	    	splitLine = line.split(" ")
	    	lineNumber = splitLine[0].strip("[]")

	    	commandAndArgs = splitLine[1].split(",")

	    	command = commandAndArgs[0]
	    	args = commandAndArgs[1:]

	    	username = args[0]
	    	if not username.startswith("./"):
		    	if username not in userActions.keys():
		    		userActions[username] = []
	    		userActions[username].append({'command': command, 'args': args, 'lineNum': lineNumber})

	return userActions

def main():
	print('reading file...')
	userActions = splitUsersFromFile()
	print('sending requests...')
	for userSpecificActions in userActions:
		sendRequests( userActions[userSpecificActions] )


if __name__ == '__main__':
	if len(sys.argv) < 4:
		print('\033[1;31;40mINCORRECT PARAMETERS\n')
		print('\033[1;32;40mpython3 testDriver.py <url (no http://)> <port> <file>')
		print('example: python3 testDriver.py localhost 8000 2userWorkLoad.txt')
		print('\033[0;37;40m')
	else:
		url = sys.argv[1]
		port = sys.argv[2]
		main()
		send('DUMPLOG', ['./testLOG'], '-1')
		print('completed')
		
