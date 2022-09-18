import sqlite3 as lite
import csv, sys, os, re, shutil, subprocess

class Builder(object):
    ''' This class builds or adds on to a pre-existing sqlite3 database '''

    def __init__(self):
        ## Create Base directory
        self.bDir = os.getcwd()

        ## Declare the DIG_INFOs directory
        self.dDir = input(f'DIG_INFOs Directory? [{self.bDir}/DIG_INFOs]\n')
        if not self.dDir:
            self.dDir = f'{self.bDir}/DIG_INFOs'
        else:
            print('')

        ## Create directory list for dDir
        self.dList = os.listdir(self.dDir)

        ## Ensure nTgts.lst is where we think it should be
        self.nTgts = input(f'List of Domains Scanned? [{self.bDir}/nTgts.lst]\n')
        if not self.nTgts:
            self.nTgts = f'{self.bDir}/nTgts.lst'
        else:
            print('')


        ## Create DB
        self.dbName = input(f'Desired name for DB? [{self.bDir}/zones.sqlite]\n')
        if not self.dbName:
            self.dbName = f'{self.bDir}/zones.sqlite'
        else:
            print('')

        ## Declare the working directory
        self.wDir = input(f'Desired name for working directory? [{self.bDir}/PARSER_FILEs]\n')
        if not self.wDir:
            self.wDir = f'{self.bDir}/PARSER_FILEs'
        else:
            print('')

        ## Check to ensure the working directory doesn't exist yet
        if os.path.isdir(self.wDir):
            self.wExists = input(f'{self.wDir} already exists, remove and continue? [y/N]\n')
            #if not self.wExists:
                #exit(1)
            if self.wExists == 'n':
                exit(1)
            elif self.wExists == 'N':
                exit(1)
            else:
                print('Removing and continuing')
                print('')
                shutil.rmtree(self.wDir)

        ## Create working and temporary directory
        os.mkdir(self.wDir)
        #self.wDir = f'{self.bDir}/PARSER_FILEs'
        os.mkdir(f'{self.wDir}/TMP_FILEs')
        self.tDir = f'{self.wDir}/TMP_FILEs'

        if os.path.isfile(self.dbName):
            self.dFile = input(f'{self.dbName} already exists\nUpdate and continue? [y/N]\n')
            if not self.dFile:
                exit(1)
            elif self.dFile == 'n':
                exit(1)
            elif self.dFile == 'N':
                exit(1)
            else:
                print(f'\nUpdating {self.dbName} and continuing')

        print(f'Proceeding to build {self.dbName}\n')
        con = lite.connect(self.dbName, isolation_level = None)
        db = con.cursor()
        with con:
            db.execute("CREATE TABLE IF NOT EXISTS axfr(dm TEXT, own TEXT, ttl TEXT, rr TEXT, data TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS dm2ns(dm TEXT, ns TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS scanned(dm TEXT, UNIQUE(dm))")
            db.execute("CREATE TABLE IF NOT EXISTS domains(dm TEXT, UNIQUE(dm))")
            db.execute("CREATE TABLE IF NOT EXISTS nameservers(ns TEXT, UNIQUE(ns))")
        con.close()


    def parser(self):
        ''' This function parses the files '''
        ## Ignore any blank lines or ;'s
        expr = re.compile('^;')

        ## Concatenate the axfr for each nameserver, for a given domain, to a domain specific file
        with open(f'{self.wDir}/axfr.lst', 'w') as aFile:
            for domain in self.dList:
                nsList = os.listdir(f'{self.dDir}/{domain}')

                ## Obtain size of list
                nsListSize = len(nsList)

                ## Make decision for parsing based upon Nameserver quantity
                if nsListSize > 1:
                    #print('Parsing {0}'.format(domain))
                    iSet = set()
                    with open(f'{self.tDir}/cFile', 'w') as oFile:
                        for ns in nsList:
                            with open(f'{self.dDir}/{domain}/{ns}', 'r') as iFile:
                                shutil.copyfileobj(iFile, oFile)

                    iFile = open(f'{self.tDir}/cFile', 'r')
                    with open(f'{self.tDir}/fFile', 'w') as fFile:
                        for row in iFile.readlines():
                            row = row.strip()
                            iSet.add(row)
                        iList = list(iSet)
                        for i in iList:
                            fFile.write(i + '\n')

                    nServer = f'{self.tDir}/fFile'
                    nQ = 'multiple'

                else:
                    # print(f'Parsing {domain}')
                    nServer = nsList[0]
                    nQ = 'single'

                ## Write the files
                # print('Writing {domain}')
                if nQ == 'single':
                    with open(f'{self.dDir}/{domain}/{nServer}', 'r') as iPut:
                        with open(f'{self.tDir}/{domain}', 'w') as oFile:
                            iList = iPut.read().splitlines()
                            for line in iList:
                                if line and not expr.match(line):
                                    oFile.write(domain + ' ' + line + '\n')
                                    aFile.write(domain + ' ' + line + '\n')

                if nQ == 'multiple':
                    with open(f'{nServer}', 'r') as iPut:
                        with open(f'{self.tDir}/{domain}', 'w') as oFile:
                            iList = iPut.read().splitlines()
                            for line in iList:
                                if line and not expr.match(line):
                                    oFile.write(domain + ' ' + line + '\n')
                                    aFile.write(domain + ' ' + line + '\n')
                    os.remove(f'{self.tDir}/fFile')
                    os.remove(f'{self.tDir}/cFile')


    def data_creation(self):
        ''' This function creates the lists db-builder needs '''
        ## Remove empty/unneeded files
        for i in os.listdir(self.tDir):
            sz = os.path.getsize(f'{self.tDir}/{i}')
            if sz == 0:
                os.remove(f'{self.tDir}/{i}')

        ## Reassign dList as a successful list
        dList = os.listdir(self.tDir)

        ## Create domains, dm2ns, ns2dm and nameservers lists
        domainsFile = open(f'{self.wDir}/domains.lst', 'w')
        dm2nsFile = open(f'{self.wDir}/dm2ns.lst', 'w')
        nameserversFile = open(f'{self.wDir}/nameservers.lst', 'w')
        for domain in dList:
            #print(self.dDir)
            #print(domain)
            nsList = os.listdir(f'{self.dDir}/{domain}')
            domainsFile.write(f'{domain.lower()}' + '\n')
            for ns in nsList:
                dm2nsFile.write(f'{domain.lower()},{ns.lower()}' + '\n')
                nameserversFile.write(f'{ns.lower()}' + '\n')
        dm2nsFile.close()
        domainsFile.close()
        nameserversFile.close()

    def sColumn(self, db, File, Table):
        ''' Update single columns
        Deal with double nameserver entries
        '''
        iFile = open(File, 'r')
        while True:
            iRow = iFile.readline().rstrip()
            if not iRow:
                break
            db.execute(f'INSERT OR IGNORE INTO {Table} VALUES(?);', (iRow,))
        iFile.close()


    def dColumn(self, con, File, Table):
        ''' Update multiple columns '''
        with open(File, 'r') as iFile:
            rows = csv.reader(iFile, delimiter=',')
            con.executemany(f"INSERT INTO '{Table}' VALUES (?, ?)", rows)


    def db_mod(self):
        # con = lite.connect(self.dbName, isolation_level = None)
        con = lite.connect(self.dbName)
        con.text_factory = str
        db = con.cursor()

        ### Insert data table
        aFile = open(f'{self.wDir}/axfr.lst', 'r')
        while True:
            row = aFile.readline().rstrip()
            if not row:
                break
            try:
                dmRow = row.split()[0].lower()
                ownRow = row.split()[1].lower()
                ttlRow = row.split()[2]
                rrRow = row.split()[4]
                data = row.split()[5:]
                dataRow = ' '.join(map(str, data))
            except:
                print(f'Issue with {row}')
                exit(1)
            db.execute("INSERT INTO axfr VALUES(?, ?, ?, ?, ?);", (dmRow, ownRow, ttlRow, rrRow, dataRow))
        aFile.close()

        ## Insert Tables
        self.dColumn(con, f'{self.wDir}/dm2ns.lst', 'dm2ns')
        self.sColumn(db, self.nTgts, 'scanned')
        self.sColumn(db, f'{self.wDir}/domains.lst', 'domains')
        self.sColumn(db, f'{self.wDir}/nameservers.lst', 'nameservers')
        con.commit()
        con.close()

        ## Remove tmp directory
        shutil.rmtree(self.wDir)

        ## Declare complete
        print('Finished!\n')
