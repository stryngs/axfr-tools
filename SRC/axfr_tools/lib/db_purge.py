import sqlite3 as lite
import csv, sys, os, re, shutil

class Purge(object):
    ''' This class is used to purge things from the DB '''

    def domain(self):
        """This function iterates through a list
        and purges any instances of a domain
        """
        pFile = raw_input('List of domains to purge?\n')
        dbFile = raw_input('Tgt DB?\n')
        with open(pFile, 'r') as iFile:
            pList = list(set(iFile.read().splitlines()))
        con = lite.connect(dbFile, isolation_level = None)    ### Test for speed
        db = con.cursor()
        count = 1

        ## Iterate through each domain finding nameservers
        with con:
            for dm in pList:

                ## Purge the easy stuff
                print 'Purging %s -- %s' % (count, dm)
                db.execute("DELETE FROM axfr WHERE dm = ?;", (dm,))
                db.execute("DELETE FROM scanned WHERE dm = ?;", (dm,))
                db.execute("DELETE FROM domains WHERE dm = ?;", (dm,))

                ## Obtain a list from dm2ns
                q = db.execute("SELECT `ns` FROM `dm2ns` WHERE LOWER(`dm`) = ?;", (dm.lower(),))
                dnList = [i[0] for i in q.fetchall()]

                ## Take dnList and play with counts
                for dn in dnList:
                    q = db.execute("SELECT COUNT(`ns`) FROM `dm2ns` WHERE LOWER(`ns`) = ?;", (dn.lower(),))
                    nCount = int(q.fetchone()[0])

                    ## Remove the entry from dm2ns
                    db.execute("DELETE FROM `dm2ns` WHERE LOWER(`dm`) = ? and LOWER(`ns`) = ?;", (dm.lower(), dn.lower()))

                    ## If nCount is 1, then it is safe to purge from nameservers
                    if nCount == 1:
                        db.execute("DELETE FROM `nameservers` WHERE LOWER(`ns`) = ?;", (dn.lower(),))
                con.commit()
                count += 1
        con.close()

        ## Declare complete
        print 'Finished!\n'
