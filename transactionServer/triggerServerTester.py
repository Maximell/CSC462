from transactionServer import Triggers

triggers = Triggers()

# Buy tests
triggers.addBuyTrigger('user1', 's', 500)
print "1 buy: ", triggers.getBuyTriggers()
triggers.addBuyTrigger('user1', 'd', 20)
triggers.setBuyActive('user1', 's', 50)
print "2 buy, 1 active: ", triggers.getBuyTriggers()
triggers.cancelBuyTrigger('user1', 's')
print "1 buy: ", triggers.getBuyTriggers()
print "should be 0: ", triggers.setBuyActive('userNA', 's', 50)
print "should be 0: ", triggers.setBuyActive('user1', 'NA', 50)
print "should be 0: ", triggers.setBuyActive('user1', 'd', 1000)
# sell tests
triggers.addSellTrigger('user1', 's', 500)
print "1 sell: ", triggers.getSellTriggers()
triggers.addSellTrigger('user1', 'd', 20)
triggers.setSellActive('user1', 's', 50)
print "2 sells, 1 active: ", triggers.getSellTriggers()
triggers.cancelSellTrigger('user1', 's')
print "1 sell: ", triggers.getSellTriggers()
print "should be 0: ", triggers.setSellActive('userNA', 's', 50)
print "should be 0: ", triggers.setSellActive('user1', 'NA', 50)
print "should be 0: ", triggers.setSellActive('user1', 'd', 1000)




