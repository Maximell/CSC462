# pip3.6 install requests
import requests
import asyncio
import sys

# Worker machines IP:Port
workerMap = [["http://142.104.91.144:44424" , 0] ,["http://142.104.91.145:44424",0]
             ,["http://142.104.91.146:44424" , 0],["http://142.104.91.147:44424" , 0]
             ,["http://142.104.91.148:44424" , 0],["http://142.104.91.149:44424" , 0]
             ,["http://142.104.91.150:44424" , 0], ["http://142.104.91.130:44424" , 0]
             ,["http://142.104.91.132:44424", 0] ,["http://142.104.91.133:44424", 0]
            , ["http://142.104.91.134:44424", 0]]
# User to Worker Mapping.
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

async def send(command, args, lineNum):
    user = args[0]
    if user in userMap:
        base_url = userMap[user]
        print("In dict already")
    else:
        min = workerMap[0][1]
        index = 0
        for x in range(0 , len(workerMap)):
            currentWorker = workerMap[x]
            if currentWorker[1] <= min:
                sendto = currentWorker
                index = x
                min = currentWorker[1]
        if sendto != None:
            print("adding User to map")
            userMap[user] = sendto[0]
            base_url = sendto[0]
            workerMap[index][1] += 1

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
        await asyncio.ensure_future( send(command['command'], command['args'], command['lineNum']) )

def splitUsersFromFile(start, chunk):
    userActions = {}
    lastLineNumber = -1
    readAmount = start + chunk

    with open(sys.argv[1]) as f:
        count = 0
        for line in f:
            if count < start:
                # apparently python file reading is already lazy, so hopefully by skipping the lines, it will be alright
                count += 1
                continue
            elif count >= readAmount:
                # TODO: check logic, that it is hitting all requests, and not cutting one short?
                return userActions, False, lastLineNumber

            splitLine = line.split(" ")
            lineNumber = splitLine[0].strip("[]")
            lastLineNumber = lineNumber

            commandAndArgs = splitLine[1].split(",")

            command = commandAndArgs[0]
            args = commandAndArgs[1:]
            # separate based on username and 'x' != 'x\n' which was happening a lot
            args[0] = args[0].strip()

            username = args[0]

            if not username.startswith("./"):
                if username not in userActions.keys():
                    userActions[username] = []
                userActions[username].append({'command': command, 'args': args, 'lineNum': lineNumber})

            count += 1

    return userActions, True, lastLineNumber

async def main():
    finished = False

    start = 0
    chunk = 10000

    while finished == False:
        print('reading file...')
        userActions, finished, lastLineNumber = splitUsersFromFile(start, chunk)
        start += chunk

        print('sending requests...')
        processes = []
        for userSpecificActions in userActions:
            processes.append(
                asyncio.ensure_future(sendRequests(userActions[userSpecificActions]))
            )

        for process in processes:
            await process

    print("last line number was calculated to be: " + str(lastLineNumber))
    await asyncio.ensure_future(
        send('DUMPLOG', ['./testLOG'], lastLineNumber)
    )


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('INCORRECT PARAMETERS\n')
        print('python3 testDriver.py <file>')
        print('example: python3 testDriver.py 2userWorkLoad.txt')
        print(sys.argv)
    else:
        base_url = None

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            main()
        )
        loop.close()

        print('completed')
		
