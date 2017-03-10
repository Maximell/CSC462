# pip3.6 install requests
import requests
import asyncio
import sys

workerMap = [["142.104.91.142:44424" , 0] ,["142.104.91.144:44424",0]]
userMap = {}

urls = {
    'ADD': '/add/%s/',
    'BUY': '/buy/%s/%s/',
    'QUOTE': '/quote/%s/%s/',
    'COMMIT_BUY': '/commit-buy/%s/',
    'CANCEL_BUY': '/cancel-buy/%s/',
    'SELL': '/sell/%s/%s/',
    'COMMIT_SELL': '/commit-sell/%s/',
    'CANCEL_SELL': '/cancel-sell/%s/',
    'SET_BUY_AMOUNT': '/set-buy-amount/%s/%s/',
    'CANCEL_SET_BUY': '/cancel-set-buy/%s/%s/',
    'SET_BUY_TRIGGER': '/set-buy-trigger/%s/%s/',
    'SET_SELL_AMOUNT': '/set-sell-amount/%s/%s/',
    'SET_SELL_TRIGGER': '/set-sell-trigger/%s/%s/',
    'CANCEL_SET_SELL': '/cancel-set-sell/%s/%s/',
    'DUMPLOG': '/dumplog/',
    'DISPLAY_SUMMARY': '/display-summary/%s/'
}

def send(command, args, lineNum):
    user = args["userId"]
    if userMap[user] != None:
        base_url = userMap["userId"]
    else:
        min = workerMap[0][1]
        for x in range(0 , len(workerMap)):
            currentWorker = workerMap[x]
            if currentWorker[1] <= min:
                sendto = currentWorker
                min = currentWorker[1]
        if sendto != None:
            userMap[args["userId"]] = sendto[0]
            base_url = sendto[0]
        else:
            print("problem with sending the workers")






    url = base_url
    data = {'lineNum': lineNum}
    if len(args) > 2:
        args = {'userId':args[0] , 'stockSymbol':args[1], 'cash':args[2]
                }
    elif len(args) == 2 and command in ['ADD']:
        args = {'userId':args[0] , 'cash':args[1]
                }
    elif len(args) == 2:
        args = {'userId':args[0] , 'stockSymbol':args[1]
                }
    elif len(args) == 1 and command in ['DUMPLOG']:
        args = {'fileName':args[0]}
    elif len(args) == 1:
        args = {'userId':args[0]}

    method = 'GET'

    if command in ['ADD']:
        url = base_url + urls[command] % (args['userId'])
        data['cash'] = args['cash']
        method = 'POST'
    if command in ['BUY', 'SELL', 'SET_BUY_AMOUNT', 'SET_BUY_TRIGGER', 'SET_SELL_AMOUNT', 'SET_SELL_TRIGGER']:
        url = base_url + urls[command] % (args['userId'], args['stockSymbol'])
        data['cash'] = args['cash']
        method = 'POST'
    if command in ['QUOTE']:
        url = base_url + urls[command] % (args['userId'], args['stockSymbol'])
        method = 'GET'
    if command in ['COMMIT_BUY', 'CANCEL_BUY', 'COMMIT_SELL', 'CANCEL_SELL']:
        url = base_url + urls[command] % (args['userId'])
        method = 'POST'
    if command in ['CANCEL_SET_BUY', 'CANCEL_SET_SELL']:
        url = base_url + urls[command] % (args['userId'], args['stockSymbol'])
        method = 'POST'
    if command in ['DUMPLOG']:
        url = base_url + urls[command]
        data['fileName'] = args['fileName']
        method = 'POST'
    if command in ['DISPLAY_SUMMARY']:
        url = base_url + urls[command] % (args['userId'])
        method = 'GET'

    print(method)
    print(url)
    print(data)
    if method == 'GET':
        r = requests.get( url, data=data , verify=False)
    else:
        r = requests.post( url, data=data , verify=False)
    print(r.status_code)

async def sendRequests(userCommandList):
    for command in userCommandList:
        send(command['command'], command['args'], command['lineNum'])

def splitUsersFromFile():
    userActions = {}
    with open(sys.argv[2]) as f:
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

async def main():
    print('reading file...')
    userActions = splitUsersFromFile()
    print('sending requests...')
    for userSpecificActions in userActions:
        asyncio.ensure_future( sendRequests( userActions[userSpecificActions] ) )


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('INCORRECT PARAMETERS\n')
        print('python3 testDriver.py <url> <file>')
        print('example: python3 testDriver.py http://localhost:8000 2userWorkLoad.txt')
        print(sys.argv)
    else:
        # get last line number. if file cant fit in memory, this will break. how large a file can fit in memory?
        lastLine = next(reversed(open(sys.argv[2]).readlines()))
        lastLineNumber = lastLine.split(" ")[0].strip("[]")

        # base_url = sys.argv[1]
        base_url = None
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.close()
        print("last line number was calculated to be: "+str(lastLineNumber))
        send('DUMPLOG', ['./testLOG'], lastLineNumber)
        print('completed')
		
