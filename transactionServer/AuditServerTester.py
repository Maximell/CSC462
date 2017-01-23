from transactionServer import AuditServer

auditServer = AuditServer()
auditServer.log('test1')
auditServer.log('test2')
auditServer.writeLogs('testAuditsFile.txt')