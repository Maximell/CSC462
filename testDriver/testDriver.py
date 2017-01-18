# pip3.6 install requests
import requests
import asyncio
import sys

async def send(command, args, lineNum):
	r = requests.post(base_url, data = {'command': command, 'args': args, 'lineNum': lineNum})
	print(r.status_code)

async def sendRequests():
	with open(sys.argv[2]) as f:
	    for line in f:
	    	splitLine = line.split(" ")
	    	lineNumber = splitLine[0]
	    	line = splitLine[1]
	    	commandAndArgs = line.split(",")

	    	command = line[0]
	    	args = line[1:]
	    	# ensure_future is a fire and forget: http://stackoverflow.com/questions/37278647/fire-and-forget-python-async-await
	    	asyncio.ensure_future(send(command, args, lineNumber))

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print("\033[1;31;40mINCORRECT PARAMETERS\n")
		print("\033[1;32;40mpython3 sendRequests.py <url> <file>")
		print("example: python3 sendRequests.py http://localhost:8000 1userWorkLoad.txt")
		print("\033[0;37;40m")
	else:
		base_url = sys.argv[1]
		loop = asyncio.get_event_loop()
		loop.run_until_complete(sendRequests())
		loop.close()



