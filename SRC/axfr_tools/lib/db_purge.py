import sqlite3 as lite
import csv, sys, os, re, shutil

class Purge(object):
    ''' This class is used to purge things from the DB '''

    def domain(self):
        """This function iterates through a list
        and purges any instances of a domain
        """
        pFile = input('List of domains to purge?\n')
        dbFile = input('Tgt DB?\n')
        with open(pFile, 'r') as iFile:
            pList = list(set(iFile.read().splitlines()))
        con = lite.connect(dbFile, isolation_level = None)
        db = con.cursor()
        count = 1
        with con:
            for dm in pList:
                print(f'Purging {count} -- {dm}')
                db.execute("DELETE FROM axfr WHERE dm = ?;", (dm,))
                db.execute("DELETE FROM scanned WHERE dm = ?;", (dm,))
                db.execute("DELETE FROM domains WHERE dm = ?;", (dm,))
                db.execute("DELETE FROM issues WHERE dm = ?;", (dm,))
                db.execute("DELETE FROM nameservers WHERE ns NOT IN (SELECT ns from dm2ns WHERE dm = ?);", (dm,))
                db.execute("DELETE FROM issues WHERE dm = ?;", (dm,))
                con.commit()
                count += 1
        con.close()
        print('Finished!\n')
