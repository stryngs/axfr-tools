import sqlite3 as lite
import csv, sys, os, re, shutil

class Queries(object):
    ''' This class is used for pre-defined queries to the DB 

    __init__() does the job of setting up our environment
    To add a module for the queries class:
    - Modify PRIOR EXISTENCE TESTS in __init__() accordingly
    - Use the following for your module from __init__():
        - self.wDir
        - self.con
        - self.db
    '''

    def __init__(self, aType):
        ''' Environment setup '''
        ### Set base dir
        bDir = os.getcwd()
        ## Set DB
        dbName = raw_input('DB to work with? [%s/MASTER.sqlite]\n' % bDir)
        if not dbName:
            dbName = '%s/MASTER.sqlite' % bDir
        else:
            print ''

        '''
        PRIOR EXISTENCE TESTS
        '''
        options = {'nameserverCount', 'domainCount'}
        if aType in options:
            self.wDir = '%s/queries' % bDir
            fName = ''
            if aType == 'domainCount':
                if os.path.isfile('%s/DomainCounts.lst' % self.wDir):
                    fName = '%s/DomainCounts.lst' % self.wDir

            if aType == 'nameserverCount':
                if os.path.isfile('%s/NameserverCounts.lst' % self.wDir):
                    fName = '%s/NameserverCounts.lst' % self.wDir

            if not os.path.isdir(self.wDir):
                os.mkdir(self.wDir)

            if fName:
                wExists = raw_input('%s already exists, continue? [y/N]\n' % fName)
                if not wExists:
                    exit(1)
                elif wExists == 'n':
                    exit(1)
                elif wExists == 'N':
                    exit(1)
                else:
                    print '\nRemoving and continuing'
                    print ''
                    os.remove(fName)
                
        if aType == 'nameserverDump':
            self.wDir = '%s/queries/nameserverDumps' % bDir
            if os.path.isdir(self.wDir):
                wExists = raw_input('%s already exists, continue? [y/N]\n' % self.wDir)
                if not wExists:
                    exit(1)
                elif wExists == 'n':
                    exit(1)
                elif wExists == 'N':
                    exit(1)
                else:
                    print '\nRemoving and continuing'
                    print ''
                    shutil.rmtree(self.wDir)
            if not os.path.isdir(self.wDir):
                os.mkdir(self.wDir)

        '''
        DB SET
        '''
        self.con = lite.connect(dbName)
        #con.text_factory = str
        self.db = self.con.cursor()


    def nameserverDump(self):
        ''' Query and dump DB for a given Nameserver's domains '''
        nServer = raw_input ('Nameserver to reverse dump?\n')
        print ''

        '''
        GRAB DOMAINS
        '''
        dSet = set()
        with self.con:
            print 'Querying domains for %s\n' % nServer
            self.db.execute("SELECT dm FROM dm2ns WHERE ns LIKE ?;", (nServer,))
            records = self.db.fetchall()

            ## Convert tuple to string
            for row in records:
                row = str(row).split("'")[1]
                dSet.add(row)

            ## List stats
            length = len(dSet)
            print '%s domains found\n' % length
            dList = list(dSet)

            '''
            EXTRACT AXFR DATA FROM DOMAINS
            '''
            count = 1
            for domain in dList:
                print 'Querying %s -- %s' % (count, domain)
                self.db.execute("SELECT own, ttl, rr, data FROM axfr WHERE dm = ?;", (domain,))
                print 'Fetching %s -- %s' % (count, domain)
                zone = self.db.fetchall()

                ## Convert tuple to string
                print 'Writing %s -- %s' % (count, domain)
                with open('%s/%s' % (self.wDir, domain), 'w') as oFile:
                    for record in zone:
                        own = str(record).split("'")[1]
                        ttl = str(record).split("'")[3]
                        rr = str(record).split("'")[5]
                        data = str(record).split("'")[7]
                        oFile.write(own + '\t' + ttl + '\t' + rr + '\t' + data + '\n')
                count += 1
                print ''

        ## Declare complete
        print 'Finished!\n'
        print 'Contents written to %s' % self.wDir


    def nameserverCount(self):
        ''' Create a sortable list of nameservers from the db

        This list shows the number of domains for the given nameserver
        '''
        tSet = set()
        with self.con:
            print 'Querying domain counts'
            self.db.execute("SELECT COUNT(*), ns FROM dm2ns GROUP by ns;")
            print 'Fetching domains'
            records = self.db.fetchall()
            
            ## Convert tuple to string
            for row in records:
                count = str(row).split("'")[0].split('(')[1].split(',')[0]
                ns = str(row).split("'")[1]
                tSet.add('%s - %s' % (count, ns))
            tList = list(tSet)

        print 'Creating list\n'
        with open('%s/NameserverCounts.lst' % self.wDir, 'w') as oFile:
                for i in tList:
                    oFile.write(i + '\n')

        ## Declare complete
        print 'Finished!\n'
        print 'High to low:  sort -g %s/NameserverCounts.lst | tac | less' % self.wDir
        print 'Low to high:  sort -g %s/NameserverCounts.lst | less\n' % self.wDir


    def domainCount(self):
        ''' Create a sortable list of domains from the db

        This list shows the number of rows for a given domain
        It is obtained from the axfr table
        '''
        tSet = set()
        with self.con:
            print 'Querying domain counts'
            self.db.execute("SELECT COUNT(*), dm FROM axfr GROUP by dm;")
            print 'Fetching domains'
            records = self.db.fetchall()
            
            ## Convert tuple to string
            for row in records:
                count = str(row).split("'")[0].split('(')[1].split(',')[0]
                dm = str(row).split("'")[1]
                tSet.add('%s - %s' % (count, dm))
            tList = list(tSet)

        print 'Creating list\n'
        with open('%s/DomainCounts.lst' % self.wDir, 'w') as oFile:
                for i in tList:
                    oFile.write(i + '\n')

        ## Declare complete
        print 'Finished!\n'
        print 'High to low:  sort -g %s/DomainCounts.lst | tac | less' % self.wDir
        print 'Low to high:  sort -g %s/DomainCounts.lst | less\n' % self.wDir
