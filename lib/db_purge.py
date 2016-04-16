import sqlite3 as lite
import csv, sys, os, re, shutil

class purge(object):
    ''' This class is used to purge things from the DB '''

    def domain(self):
        ''' This function iterates through a list and purges instances of a domain

        The one table it does not touch is the nameserver table
        '''
        pFile = raw_input('List of domains to purge?\n')
        dbFile = raw_input('Tgt DB?\n')
        pSet = set()
        with open(pFile, 'r') as iFile:
            lines = iFile.readlines()
            for i in lines:
                pSet.add(i.strip())
        pList = list(pSet)
        con = lite.connect(dbFile)
        db = con.cursor()
        count = 1
        with con:
            for dm in pList:
                print 'Purging %s -- %s' % (count, dm)
                db.execute("DELETE FROM axfr WHERE dm = ?;", (dm,))
                db.execute("DELETE FROM dm2ns WHERE dm = ?;", (dm,))
                db.execute("DELETE FROM domains WHERE dm = ?;", (dm,))
                db.execute("DELETE FROM scanned WHERE dm = ?;", (dm,))
                count += 1

        ## Declare complete
        print 'Finished!\n'


