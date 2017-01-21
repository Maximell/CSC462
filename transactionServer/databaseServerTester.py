from transactionServer import databaseServer
import time

print databaseServer
database = databaseServer(transactionExpire=2)
print "\nstarting user/cash functions:\n"
user = database.getUser('test')
print 'user should be null: ' + str(user)
print database.addUser('user1')
print database.addUser('user2')
print database.addCash('user1', 75.67)
print database.addCash('user1', 25.00)
print database.getUser('user1')
print database.getUser('user2')
print database.reserveCash('user2', 5)
print database.reserveCash('user1', 75)
print database.reserveCash('user1', 30)
print database.releaseCash('user1', 75)
print database.releaseCash('user1', 1)

print "\nstarting buy/sell functions:\n"
database.pushBuy('user1', 'abc', 3)
database.pushBuy('user1', 'bca', 1)
print "2 buys: ", database._checkBuys('user1')
database.popBuy('user1')
print "1 buy: ", database._checkBuys('user1')
buyObject = database.popBuy('user1')
print "empty: ", database._checkBuys('user1')
database.popBuy('user1') # extra pop shouldnt throw error

print "is buy active (should be true)", database.isBuySellActive(buyObject)
print "sleeping for 3 seconds"
time.sleep(3)
print "is buy active (should be false)", database.isBuySellActive(buyObject)

database.pushSell('user1', 'abc', 3)
database.pushSell('user1', 'bca', 1)
print "2 sells: ", database._checkSells('user1')
database.popSell('user1')
print "1 sells: ", database._checkSells('user1')
sellObject = database.popSell('user1')
print "empty: ", database._checkSells('user1')
database.popSell('user1') # extra pop shouldnt throw error

print "is sell active (should be true)", database.isBuySellActive(sellObject)
print "sleeping for 3 seconds"
time.sleep(3)
print "is sell active (should be false)", database.isBuySellActive(sellObject)

print "pushSell non existant user: ", database.pushSell('userNA', 'abc', 3)
print "pushBuy non existant user: ", database.pushBuy('userNA', 'abc', 3)
print "popSell non existant user: ", database.popSell('userNA')
print "popBuy non existant user: ", database.popBuy('userNA')