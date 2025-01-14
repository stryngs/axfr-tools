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
        bDir = os.getcwd()
        dbName = input(f'DB to work with? [{bDir}/example.sqlite3]\n')
        if not dbName:
            dbName = f'{bDir}/example.sqlite3'
        else:
            print('')

        '''
        PRIOR EXISTENCE TESTS
        '''
        options = {'nameserverCount', 'domainCount'}
        if aType in options:
            self.wDir = f'{bDir}/queries'
            fName = ''
            if aType == 'domainCount':
                if os.path.isfile(f'{self.wDir}/DomainCounts.lst'):
                    fName = f'{self.wDir}/DomainCounts.lst'

            if aType == 'nameserverCount':
                if os.path.isfile(f'{self.wDir}/NameserverCounts.lst'):
                    fName = f'{self.wDir}/NameserverCounts.lst'

            if not os.path.isdir(self.wDir):
                os.mkdir(self.wDir)

            if fName:
                wExists = input(f'{fName} already exists, continue? [y/N]\n')
                if not wExists:
                    exit(1)
                elif wExists == 'n':
                    exit(1)
                elif wExists == 'N':
                    exit(1)
                else:
                    print('\nRemoving and continuing')
                    print('')
                    os.remove(fName)

        if aType == 'nameserverDump':
            self.wDir = f'{bDir}/queries/nameserverDumps'
            if os.path.isdir(self.wDir):
                wExists = input(f'{self.wDir} already exists, continue? [y/N]\n')
                if not wExists:
                    exit(1)
                elif wExists.lower() == 'n':
                    exit(1)
                else:
                    print('\nRemoving and continuing')
                    print('')
                    shutil.rmtree(self.wDir)
            if not os.path.isdir(self.wDir):
                os.makedirs(self.wDir)

        '''
        DB SET
        '''
        self.con = lite.connect(dbName, isolation_level = None)
        self.db = self.con.cursor()


    def nameserverDump(self):
        ''' Query and dump DB for a given Nameserver's domains '''
        nServer = input('Nameserver to reverse dump?\n')
        print('')

        '''
        GRAB DOMAINS
        '''
        dSet = set()
        with self.con:
            print(f'Querying domains for {nServer}\n')
            self.db.execute("SELECT dm FROM dm2ns WHERE ns LIKE ?;", (nServer,))
            records = self.db.fetchall()

            ## Convert tuple to string
            for row in records:
                row = str(row).split("'")[1]
                dSet.add(row)

            ## List stats
            length = len(dSet)
            print(f'{length} domains found\n')
            dList = list(dSet)

            '''
            EXTRACT AXFR DATA FROM DOMAINS
            '''
            count = 1
            for domain in dList:
                print(f'Querying {count} -- {domain}')
                self.db.execute("SELECT rec, ttl, rt, data FROM axfr WHERE dm = ?;", (domain,))
                print(f'Fetching {count} -- {domain}')
                zone = self.db.fetchall()

                ## Convert tuple to string
                print(f'Writing {count} -- {domain}')
                with open(f'{self.wDir}/{domain}', 'w') as oFile:
                    for record in zone:
                        if record[0] is not None:
                            rec = record[0]
                        else:
                            rec = ''
                        if record[1] is not None:
                            ttl = str(record[1])
                        else:
                            rec = ''
                        if record[2] is not None:
                            rt = record[2]
                        else:
                            rt = ''
                        if record[3] is not None:
                            data = record[3]
                        else:
                            data = ''
                        oFile.write(rec + '\t' + ttl + '\t' + rt + '\t' + data + '\n')
                count += 1
                print('')
        print('Finished!\n')
        print(f'Contents written to {self.wDir}')


    def nameserverCount(self):
        ''' Create a sortable list of nameservers from the db

        This list shows the number of domains for the given nameserver
        '''
        tSet = set()
        with self.con:
            print('Querying domain counts')
            self.db.execute("SELECT COUNT(*), ns FROM dm2ns GROUP by ns;")
            print('Fetching domains')
            records = self.db.fetchall()

            ## Convert tuple to string
            for row in records:
                count = str(row).split("'")[0].split('(')[1].split(',')[0]
                ns = str(row).split("'")[1]
                tSet.add(f'{count} - {ns}')
            tList = list(tSet)

        print('Creating list\n')
        with open(f'{self.wDir}/NameserverCounts.lst', 'w') as oFile:
                for i in tList:
                    oFile.write(i + '\n')
        print('Finished!\n')
        print(f'High to low:  sort -g {self.wDir}/NameserverCounts.lst | tac | less')
        print(f'Low to high:  sort -g {self.wDir}/NameserverCounts.lst | less\n')


    def domainCount(self):
        ''' Create a sortable list of domains from the db

        This list shows the number of rows for a given domain
        It is obtained from the axfr table
        '''
        tSet = set()
        with self.con:
            print('Querying domain counts')
            self.db.execute("SELECT COUNT(*), dm FROM axfr GROUP by dm;")
            print('Fetching domains')
            records = self.db.fetchall()

            ## Convert tuple to string
            for row in records:
                count = str(row).split("'")[0].split('(')[1].split(',')[0]
                dm = str(row).split("'")[1]
                tSet.add(f'{count} - {dm}')
            tList = list(tSet)

        print('Creating list\n')
        with open(f'{self.wDir}/DomainCounts.lst', 'w') as oFile:
                for i in tList:
                    oFile.write(i + '\n')
        print('Finished!\n')
        print(f'High to low:  sort -g {self.wDir}/DomainCounts.lst | tac | less')
        print(f'Low to high:  sort -g {self.wDir}/DomainCounts.lst | less\n')
