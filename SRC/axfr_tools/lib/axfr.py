import dns.zone
import dns.resolver
import dns.query
import dns.rdatatype
import sqlite3 as lite
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
                   CREATE TABLE IF NOT EXISTS domains (dm TEXT)
                   """)
        db.execute("""
                   CREATE TABLE IF NOT EXISTS scanned (dm TEXT)
                   """)
        con.commit()
        con.close()


    def axfr(self, address):
        """Grab the AXFR and store it"""
        with self.db_lock:
            self.tCounter += 1
        zSet = set()
        try:
            sAxfr = False

            ## Obtain NS and iterate
            ns_answer = dns.resolver.resolve(address, 'NS')
            nSeen = False
            for server in ns_answer:
                
                ## Rely on IP
                ip_answer = dns.resolver.resolve(server.target, 'A')
                for ip in ip_answer:
                    try:
                        outer = dns.query.xfr(str(ip), address, timeout = 3)
                        zone = dns.zone.from_xfr(outer)
                        sAxfr = True
                        if nSeen is False:
                            with self.db_lock:
                                self.sCounter += 1
                            nSeen = True

                        ## Record NS
                        res = self.nDict.get(address)
                        if res is None:
                            newVal = ['.'.join(server.to_text().split('.')[0:-1])]
                            self.nDict.update({address: newVal})
                        else:
                            newVal = ['.'.join(server.to_text().split('.')[0:-1])]
                            self.nDict.update({address: res + newVal})

                        ## Parse the zone
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
                    except Exception as e:
                        return sAxfr
        except Exception as e:
            return sAxfr
        self.zDict.update({address: zSet})
        return sAxfr


    def axfrWrapper(self, hostname, timeout = 3):
        """Wrapper to run axfr with a timeout"""
        result = [None]

        def target():
            result[0] = self.axfr(hostname)

        ## Sub a thread for the axfr
        thread = threading.Thread(target = target)
        thread.start()
        thread.join(timeout)

        ## No zombies
        if thread.is_alive():
            return None
        else:
            return result[0]


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
            print(f'{self.sCounter} @ {sPer:.2f}% of {self.tCount} in {int(time.time() - self.iTime) / 60} minutes')
        except:
            pass


    def save_to_db(self, hostname, res, dbName = 'example.sqlite3'):
        """Store the findings"""
        with self.db_lock:
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
            if res is True:
                db.execute('INSERT INTO domains (dm) VALUES (?)', (hostname,))
            con.commit()
            con.close()


    def worker(self):
        """Grab the individual AXFR"""
        while True:
            try:
                sPer = (self.sCounter / self.tCounter) * 100
            except:
                sPer = 0
            if (time.time() - self.lTime) > 10:
                print(f'{self.tCount - self.tCounter}/{self.tCount} [{self.sCounter} of {self.tCounter} @ {int(time.time() - self.iTime) / 60:.2f} minutes ~ {sPer:.2f}% success so far]')
                with self.db_lock:
                    self.lTime = time.time()
            hostname = self.db_queue.get()
            if hostname is None:
                self.db_queue.task_done()
                break
            if len(hostname) > 0:
                ### Hardcoding here on example.sqlite3, fix later
                con = lite.connect('example.sqlite3', check_same_thread = False)
                db = con.cursor()
                db.execute('INSERT INTO scanned (dm) VALUES (?)', (hostname,))
                con.commit()
                con.close()
                res = self.axfrWrapper(hostname)
                if res:
                    self.save_to_db(hostname, res)
            time.sleep(.001)
            self.db_queue.task_done()
