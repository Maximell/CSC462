from Events import Event



# commit_buy
testEvent = Event(
				eventType=Event.eventTypes['errorEvent'],
				timeStamp=1234,
				server='testServ',
				transactionNum=1,
				userId='testUser',
				commandName='commit_buy',
				errorMessage='couldn\'t find testUser'
			)

print testEvent.serialize()

secondEvent = Event(**testEvent.serialize())

print secondEvent.serialize()
