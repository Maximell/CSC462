from transactionServer import databaseServer

print databaseServer
database = databaseServer()
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