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
        self.con = lite.connect(dbName, check_same_thread = False)
        db = self.con.cursor()
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
        self.con.commit()


    def axfr(self, address):
        """Grab the AXFR and store it"""
        zSet = set()
        try:
            sAxfr = False

            ## Obtain NS and iterate
            ns_answer = dns.resolver.resolve(address, 'NS')
            for server in ns_answer:
                
                ## Rely on IP
                ip_answer = dns.resolver.resolve(server.target, 'A')
                for ip in ip_answer:
                    try:
                        zone = dns.zone.from_xfr(dns.query.xfr(str(ip), address))
                        sAxfr = True

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
                        continue
            if sAxfr is True:
                with self.db_lock:
                    self.sCounter += 1
        except Exception as e:
            # print(e)
            pass
        self.zDict.update({address: zSet})
        with self.db_lock:
            self.tCounter += 1


    def save_to_db(self, hostname, dbName = 'example.sqlite3'):
        """Store the findings"""
        with self.db_lock:
            con = lite.connect(dbName, check_same_thread = False)
            db = con.cursor()
            if type(hostname) == list:
                hostname = hostname[0]
            for entry in self.zDict.get(hostname):
                db.execute('INSERT INTO axfr (dm, own, ttl, rr, data) VALUES (?, ?, ?, ?, ?)', 
                            (hostname, entry[0], entry[2], entry[1], entry[3]))
            if self.nDict.get(hostname) is not None:
                for entry in self.nDict.get(hostname):
                    db.execute('INSERT INTO dm2ns (dm, ns) VALUES (?, ?)',
                                (hostname, entry))
            con.commit()
            con.close()


    def worker(self, db_queue, axfr_instance):
        """Grab the individual AXFR"""
        while True:
            if axfr_instance.tCounter % axfr_instance.vNum == 0:
                try:
                    sPer = (axfr_instance.sCounter / axfr_instance.tCounter) * 100
                except:
                    sPer = 0
                print(f'{axfr_instance.sCounter} | {axfr_instance.tCount - axfr_instance.tCounter} | {sPer:.2f}%')
            hostname = db_queue.get()
            if hostname is None:
                break
            axfr_instance.axfr(hostname)
            axfr_instance.save_to_db(hostname)
            time.sleep(.001)
            db_queue.task_done()


    def process_file(self, file_path, db_queue, axfr_instance, max_concurrent):
        """Process the input and thread it out"""
        with open(file_path, 'r') as file:
            hostnames = file.readlines()

        ## Counts
        axfr_instance.tCount = len(hostnames)
        if axfr_instance.tCount >= 1000000:
            axfr_instance.vNum = 10000
        if axfr_instance.tCount <= 100000:
            axfr_instance.vNum = 1000
        if axfr_instance.tCount <= 10000:
            axfr_instance.vNum = 100
        if axfr_instance.tCount <= 1000:
            axfr_instance.vNum = 50

        ## Thread it out
        for hostname in [hostname.strip() for hostname in hostnames]:
            db_queue.put(hostname)
        threads = []
        for _ in range(max_concurrent):
            t = threading.Thread(target = self.worker, args = (db_queue, axfr_instance))
            t.start()
            threads.append(t)

        ## Tidy up
        db_queue.join()
        for _ in range(max_concurrent):
            db_queue.put(None)
        for t in threads:
            t.join()

        ## Final stats
        print('~~~~~~~~~~~~~~\nFinal stats:')
        sPer = (axfr_instance.sCounter / axfr_instance.tCounter) * 100
        print(f'{axfr_instance.sCounter} @ {sPer:.2f}% of {axfr_instance.tCount}')
