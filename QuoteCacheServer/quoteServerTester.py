from transactionServer import Quotes
import time

quotes = Quotes(testing=True, cacheExpire=2)

print "TEST: NO CACHE\n", quotes.getQuote("hello", "usr"), "\n"
print "TEST: CACHE\n", quotes.getQuote("hello", "usr"), "\n"
print "TEST: NO CACHE\n", quotes.getQuoteNoCache("hello", "usr"), "\n"

print "sleeping for 3 seconds..."
time.sleep(3) # delays for 3 seconds

print "TEST: EXPIRED CACHE\n", quotes.getQuote("hello", "usr"), "\n"
print "TEST: CACHE\n", quotes.getQuote("hello", "usr"), "\n"

