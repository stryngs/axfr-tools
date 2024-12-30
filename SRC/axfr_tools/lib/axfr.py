import dns.zone
import dns.resolver
import dns.query
import dns.rdatatype
import os
import sqlite3 as lite
import sys
import threading
import time
from queue import Queue

class Axfr():
    """Grab the zonefile and do something with it"""
    def __init__(self, dbName = 'example.sqlite3'):
        self.zDict = {}
        self.nDict = {}
        self.db_lock = threading.Lock()
        self.sCounter = 0
        self.tCounter = 0
        self.tCount = 0
        self.iTime = time.time()
        self.lTime = self.iTime
        self.db_queue = Queue()
        with self.db_lock:
            con = lite.connect(dbName, check_same_thread = False)
            db = con.cursor()
            db.execute("""
                    CREATE TABLE IF NOT EXISTS axfr (dm TEXT,
                                                        own TEXT,
                                                        ttl INTEGER,
                                                        rr TEXT,
                                                        data TEXT)
                    """)
            db.execute("""
                    CREATE TABLE IF NOT EXISTS dm2ns (dm TEXT, ns TEXT)
                    """)
            db.execute("""
                    CREATE TABLE IF NOT EXISTS domains (dm TEXT UNIQUE)
                    """)
            db.execute("""
                    CREATE TABLE IF NOT EXISTS scanned (dm TEXT UNIQUE)
                    """)
            db.execute("""
                    CREATE TABLE IF NOT EXISTS issues (dm TEXT, ns TEXT, err TEXT)
                    """)
            con.commit()
            con.close()


    def axfr(self, address):
        """Grab the AXFR and store it"""
        with self.db_lock:
            self.tCounter += 1
        nSet = set()
        ns_answer = None
        try:
            ns_answer = dns.resolver.resolve(address, 'NS')
        except Exception as e:
            with self.db_lock:
                con = lite.connect('example.sqlite3', check_same_thread = False)
                db = con.cursor()
                db.execute('INSERT INTO issues (dm, ns, err) VALUES (?, ?, ?)', 
                            (address, None, str(e)))
                con.commit()
                con.close()

        if ns_answer is not None:
            try:
                for server in ns_answer:
                    ip_answer = dns.resolver.resolve(server.target, 'A')
                    zone = self.axfrWrapper(ip_answer[0], address)
                    if zone[0] is not None:
                        zSet = self.axfrParser(ip_answer[0], address, server, zone[0])
                        if zSet is not None:
                            nSet = nSet|zSet
                    else:
                        if zone[1] == 'alive':
                            return (False, 'alive')
                        else:
                            return (False, 'dead')
            except Exception as e:
                with self.db_lock:
                    con = lite.connect('example.sqlite3', check_same_thread = False)
                    db = con.cursor()
                    db.execute('INSERT INTO issues (dm, ns, err) VALUES (?, ?, ?)', 
                                (address, ','.join([i.target.to_text() for i in ns_answer]), str(e)))
                    con.commit()
                    con.close()
            if len(nSet) > 0:
                self.zDict.update({address: nSet})
                return (True, True)
            else:
                return (False, 1)
        else:
            return (False, 2)


    def axfrGrab(self, ip, address):
        """Query for the zonefile"""
        qry =  dns.query.xfr(str(ip), address)
        try:
            zone = dns.zone.from_xfr(qry)
        except Exception as E:
            return None
        return zone


    def axfrParser(self, ip, address, server, zone):
        """Parse the zonefile"""
        ## Record NS
        res = self.nDict.get(address)
        if res is None:
            newVal = ['.'.join(server.to_text().split('.')[0:-1])]
            self.nDict.update({address: newVal})
        else:
            newVal = ['.'.join(server.to_text().split('.')[0:-1])]
            self.nDict.update({address: res + newVal})

        ## Parse the zone
        zSet = set()
        for host in zone.nodes.keys():
            node = zone[host]
            for rdataset in node.rdatasets:
                record_type = dns.rdatatype.to_text(rdataset.rdtype)
                record_info = {"own": host.to_text(),
                                "rr": record_type,
                                "ttl": rdataset.ttl,
                                "data": []}

                ## Record types
                if record_type == "A":
                    for ip in rdataset:
                        record_info["data"] = str(ip)
                elif record_type == "AAAA":
                    for ip in rdataset:
                        record_info["data"] = str(ip)
                elif record_type == "MX":
                    for mx in rdataset:
                        info = {"own": host.to_text(),
                                "rr": record_type,
                                "ttl": rdataset.ttl,
                                "data": f'{mx.preference} {mx.exchange}'}
                        zSet.add((info.get('own'),
                                  info.get('type'),
                                  info.get('ttl'),
                                  info.get('data')))
                elif record_type == "CNAME":
                    for cname in rdataset:
                        record_info["data"] = str(cname)
                elif record_type == "NS":
                    for ns in rdataset:
                        record_info["data"] = str(ns.target.to_text())
                elif record_type == "TXT":
                    for txt in rdataset:
                        record_info["data"] = str(txt)
                else:
                    record_info["data"] = str(rdataset)
                if record_type != 'MX':
                    zSet.add((record_info.get('own'),
                              record_info.get('rr'),
                              record_info.get('ttl'),
                              record_info.get('data')))
        return zSet


    def axfrWrapper(self, ip, address, timeout = 10):
        """Wrapper to run axfr parser with a timeout"""
        result = [None]

        def target():
            result[0] = self.axfrGrab(ip, address)

        ## Sub a thread for the axfr
        thread = threading.Thread(target = target)
        thread.start()
        thread.join(timeout)

        ## No zombies
        if thread.is_alive():
            return (None, 'alive')
        else:
            return (result[0], 'dead')


    def process_file(self, file_path, max_concurrent):
        """Process the input and thread it out"""
        with open(file_path, 'r') as file:
            hostnames = file.readlines()

        ## Thread it out
        count = 0
        for c in hostnames:
            if len(c) > 0:
                count += 1
        self.tCount = count
        for hostname in [hostname.strip() for hostname in hostnames]:
            if len(hostname) > 0:
                self.db_queue.put(hostname)
        threads = []
        for _ in range(max_concurrent):
            t = threading.Thread(target = self.worker)
            t.start()
            threads.append(t)

        ## Tidy up
        for _ in range(max_concurrent):
            self.db_queue.put(None)
        self.db_queue.join()
        for t in threads:
            t.join()

        ## Final stats
        try:
            print('~~~~~~~~~~~~~~\nFinal stats:')
            sPer = (self.sCounter / self.tCounter) * 100
            print(f'{self.sCounter} @ {sPer:.2f}% of {self.tCount} in {int(time.time() - self.iTime) / 60:.2f} minutes')
        except:
            pass

        ## Deal with any strays
        time.sleep(3)
        os._exit(0)
        


    def save_to_db(self, hostname, res, dbName = 'example.sqlite3'):
        """Store the findings"""
        with self.db_lock:
            self.sCounter += 1
            con = lite.connect(dbName, check_same_thread = False)
            db = con.cursor()
            if type(hostname) == list:
                hostname = hostname[0]
            try:
                for entry in self.zDict.get(hostname):
                    db.execute('INSERT INTO axfr (dm, own, ttl, rr, data) VALUES (?, ?, ?, ?, ?)', 
                                (hostname, entry[0], entry[2], entry[1], entry[3]))
            except:
                pass
            if self.nDict.get(hostname) is not None:
                for entry in self.nDict.get(hostname):
                    db.execute('INSERT INTO dm2ns (dm, ns) VALUES (?, ?)',
                                (hostname, entry))
            con.commit()
            try:
                db.execute('INSERT INTO domains (dm) VALUES (?)', (hostname,))
                con.commit()
            except:
                pass
            con.close()


    def worker(self):
        """Grab the individual AXFR"""
        while True:
            try:
                sPer = (self.sCounter / self.tCounter)
            except:
                sPer = 0
            if (time.time() - self.lTime) > 10:
                print(f'{self.tCount - self.tCounter}/{self.tCount} [{self.sCounter} of {self.tCounter} @ {int(time.time() - self.iTime) / 60:.2f} minutes ~ {sPer:.2f}% average success]')
                with self.db_lock:
                    self.lTime = time.time()
            hostname = self.db_queue.get()
            if hostname is None:
                self.db_queue.task_done()
                break
            if len(hostname) > 0:
                ### Hardcoding here on example.sqlite3, fix later
                with self.db_lock:
                    con = lite.connect('example.sqlite3', check_same_thread = False)
                    db = con.cursor()
                    try:
                        db.execute('INSERT INTO scanned (dm) VALUES (?)', (hostname,))
                        con.commit()
                    except:
                        pass
                    con.close()
                res = self.axfr(hostname)
                if res[0] is True:
                    self.save_to_db(hostname, res)
                else:
                    if res[1] == 'alive':
                        with self.db_lock:
                            con = lite.connect('example.sqlite3', check_same_thread = False)
                            db = con.cursor()
                            db.execute('INSERT INTO issues (dm, ns, err) VALUES (?, ?, ?)', 
                                        (hostname, None, 'hungAxfr'))
                            con.commit()
                            con.close()
            time.sleep(.001)
            self.db_queue.task_done()
