import sqlite3 as lite
import csv, sys, os, re, shutil, subprocess

class Builder(object):
    ''' This class builds or adds on to a pre-existing sqlite3 database '''

    def __init__(self):
        ## Create Base directory
        self.bDir = os.getcwd()

        ## Declare the DIG_INFOs directory
        self.dDir = raw_input('DIG_INFOs Directory? [%s/DIG_INFOs]\n' % self.bDir)
        if not self.dDir:
            self.dDir = '%s/DIG_INFOs' % self.bDir
        else:
            print ''

        ## Create directory list for dDir
        self.dList = os.listdir(self.dDir)

        ## Ensure nTgts.lst is where we think it should be
        self.nTgts = raw_input('List of Domains Scanned? [%s/nTgts.lst]\n' % self.bDir)
        if not self.nTgts:
            self.nTgts = '%s/nTgts.lst' % self.bDir
        else:
            print ''
        

        ## Create DB
        self.dbName = raw_input('Desired name for DB? [%s/zones.sqlite]\n' % self.bDir)
        if not self.dbName:
            self.dbName = '%s/zones.sqlite' % self.bDir
        else:
            print ''

        ## Declare the working directory
        self.wDir = raw_input('Desired name for working directory? [%s/PARSER_FILEs]\n' % self.bDir)
        if not self.wDir:
            self.wDir = '%s/PARSER_FILEs' % self.bDir
        else:
            print ''

        ## Check to ensure the working directory doesn't exist yet
        if os.path.isdir(self.wDir):
            self.wExists = raw_input('%s already exists, remove and continue? [y/N]\n' % self.wDir)
            #if not self.wExists:
                #exit(1)
            if self.wExists == 'n':
                exit(1)
            elif self.wExists == 'N':
                exit(1)
            else:
                print 'Removing and continuing'
                print ''
                shutil.rmtree(self.wDir)

        ## Create working and temporary directory
        os.mkdir(self.wDir)
        #self.wDir = '%s/PARSER_FILEs' % self.bDir
        os.mkdir('%s/TMP_FILEs' % self.wDir)
        self.tDir = '%s/TMP_FILEs' % self.wDir

        if os.path.isfile(self.dbName):
            self.dFile = raw_input('%s already exists\nUpdate and continue? [y/N]\n' % self.dbName)
            if not self.dFile:
                exit(1)
            elif self.dFile == 'n':
                exit(1)
            elif self.dFile == 'N':
                exit(1)
            else:
                print '\nUpdating %s and continuing' % self.dbName

        print 'Proceeding to build %s\n' % self.dbName
        con = lite.connect(self.dbName, isolation_level = None)
        db = con.cursor()
        with con:
            db.execute("CREATE TABLE IF NOT EXISTS axfr(dm TEXT, own TEXT, ttl TEXT, rr TEXT, data TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS dm2ns(dm TEXT, ns TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS scanned(dm TEXT, UNIQUE(dm))")
            db.execute("CREATE TABLE IF NOT EXISTS domains(dm TEXT, UNIQUE(dm))")
            db.execute("CREATE TABLE IF NOT EXISTS nameservers(ns TEXT, UNIQUE(ns))")
        con = None


    def parser(self):
        ''' This function parses the files '''
        ## Ignore any blank lines or ;'s
        expr = re.compile('^;')
        
        ## Concatenate the axfr for each nameserver, for a given domain, to a domain specific file
        with open('%s/axfr.lst' % self.wDir, 'w') as aFile:
            for domain in self.dList:
                nsList = os.listdir('%s/%s' % (self.dDir, domain))

                ## Obtain size of list
                nsListSize = len(nsList)

                ## Make decision for parsing based upon Nameserver quantity
                if nsListSize > 1:
                    #print 'Parsing %s' % domain
                    iSet = set()
                    with open('%s/cFile' % self.tDir, 'w') as oFile:
                        for ns in nsList:
                            with open('%s/%s/%s' % (self.dDir, domain, ns), 'r') as iFile:
                                shutil.copyfileobj(iFile, oFile)

                    iFile = open('%s/cFile' % self.tDir, 'r')
                    with open('%s/fFile' % self.tDir, 'w') as fFile:
                        for row in iFile.readlines():
                            row = row.strip()
                            iSet.add(row)
                        iList = list(iSet)
                        for i in iList:
                            fFile.write(i + '\n')

                    nServer = '%s/fFile' % self.tDir
                    nQ = 'multiple'

                else:
                    #print 'Parsing %s' % domain
                    nServer = nsList[0]
                    nQ = 'single'

                ## Write the files
                #print 'Writing %s' % domain
                if nQ == 'single':
                    with open('%s/%s/%s' % (self.dDir, domain, nServer), 'r') as iPut:
                        with open('%s/%s' % (self.tDir, domain), 'w') as oFile:
                            iList = iPut.read().splitlines()
                            for line in iList:
                                if line and not expr.match(line):
                                    oFile.write(domain + ' ' + line + '\n')
                                    aFile.write(domain + ' ' + line + '\n')

                if nQ == 'multiple':
                    with open('%s' % nServer, 'r') as iPut:
                        with open('%s/%s' % (self.tDir, domain), 'w') as oFile:
                            iList = iPut.read().splitlines()
                            for line in iList:
                                if line and not expr.match(line):
                                    oFile.write(domain + ' ' + line + '\n')
                                    aFile.write(domain + ' ' + line + '\n')
                    os.remove('%s/fFile' % self.tDir)
                    os.remove('%s/cFile' % self.tDir)


    def data_creation(self):
        ''' This function creates the lists db-builder needs '''
        ## Remove empty/unneeded files
        for i in os.listdir(self.tDir):
            sz = os.path.getsize('%s/%s' % (self.tDir, i))
            if sz == 0:
                os.remove('%s/%s' % (self.tDir, i))

        ## Reassign dList as a successful list
        dList = os.listdir(self.tDir)

        ## Create domains, dm2ns, ns2dm and nameservers lists
        domainsFile = open('%s/domains.lst' % self.wDir, 'w')
        dm2nsFile = open('%s/dm2ns.lst' % self.wDir, 'w')
        nameserversFile = open('%s/nameservers.lst' % self.wDir, 'w')
        for domain in dList:
            #print self.dDir
            #print domain
            nsList = os.listdir('%s/%s' % (self.dDir, domain))
            domainsFile.write('%s' % (domain.lower()) + '\n')
            for ns in nsList:
                dm2nsFile.write('%s,%s' % (domain.lower(), ns.lower()) + '\n')
                nameserversFile.write('%s' % (ns.lower()) + '\n')
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
            db.execute("INSERT OR IGNORE INTO %s VALUES(?);" % Table, (iRow,))
        iFile.close()


    def dColumn(self, con, File, Table):
        ''' Update multiple columns '''
        with open(File, 'r') as iFile:
            rows = csv.reader(iFile, delimiter=',')
            con.executemany("INSERT INTO '%s' VALUES (?, ?)" % Table, rows)


    def db_mod(self):
        con = lite.connect(self.dbName, isolation_level = None)
        con.text_factory = str
        db = con.cursor()

        with con:
            ### Insert data table
            aFile = open('%s/axfr.lst' % self.wDir, 'r')
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
                    print 'Issue with %s' % row
                    exit(1)
                db.execute("INSERT INTO axfr VALUES(?, ?, ?, ?, ?);", (dmRow, ownRow, ttlRow, rrRow, dataRow))
            aFile.close()
            
            ## Insert Tables
            self.dColumn(con, '%s/dm2ns.lst' % self.wDir, 'dm2ns')
            self.sColumn(db, self.nTgts, 'scanned')
            self.sColumn(db, '%s/domains.lst' % self.wDir, 'domains')
            self.sColumn(db, '%s/nameservers.lst' % self.wDir, 'nameservers')

        ## Remove tmp directory
        shutil.rmtree(self.wDir)

        ## Declare complete
        print 'Finished!\n'
