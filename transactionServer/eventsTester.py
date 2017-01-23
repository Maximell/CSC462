from Events import BaseEvent, QuoteServerEvent, AccountTransactionEvent

#baseEvent = BaseEvent('123', 'testServer', '1', 'user1', testArg1='testArg1', testArg2='testArg2')
#print baseEvent.serialize()

quoteServerEvent = QuoteServerEvent('1234', 'testServer2', '2', 'user2', quoteServerTime='12345', stockSymbol='abc', price='45', cryptoKey='somecryptokey')
print quoteServerEvent.serialize()

accountTransactionEvent = AccountTransactionEvent

