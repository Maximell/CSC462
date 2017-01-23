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
database.pushBuy('user1', 'abc', 3, 20)
database.pushBuy('user1', 'bca', 1, 20)
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

database.pushSell('user1', 'abc', 3, 20)
database.pushSell('user1', 'bca', 1, 20)
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

print "pushSell non existant user: ", database.pushSell('userNA', 'abc', 3, 20)
print "pushBuy non existant user: ", database.pushBuy('userNA', 'abc', 3, 20)
print "popSell non existant user: ", database.popSell('userNA')
print "popBuy non existant user: ", database.popBuy('userNA')

print "\nstarting portfolio functions:\n"
print "shouldnt be able to remove from portfolio we dont have: ", database.removeFromPortfolio('user1', 'abc', 3)
print "unfound user: ", database.removeFromPortfolio('userNA', 'abc', 3)

print "cant add to portfolio of person we dont have: ", database.addToPortfolio('userNA', 'abc', 2)
print "add 2 to portfolio: ", database.addToPortfolio('user1', 'abc', 4)
print "cant remove more portfolio then we own: ", database.removeFromPortfolio('user1', 'abc', 5)
print "successfully remove 1 (leaving 3): ", database.removeFromPortfolio('user1', 'abc', 1)
database.addToPortfolio('user1', 'xyz', 7)
print "should have 2 in portfolio: ", database.checkPortfolio('user1')
database.reserveFromPortfolio('user1', 'xyz', 3)
print "reserved 3 from xyz: ", database.checkPortfolio('user1')
database.releasePortfolioReserves('user1', 'xyz', 1)
print "released 1 from xyz reserves: ", database.checkPortfolio('user1')
database.commitReservedPortfolio('user1', 'xyz', 2)
print "commit 2 from xyz reserves: ", database.checkPortfolio('user1')
