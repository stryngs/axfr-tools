import os
import time

class Dig(object):
    """Wrapper class for the dig-em bash script"""
    
    def dig(self, domain):
        os.system('dig-em -d %s python' % domain)

    def xdomainParser(self, q):
        domain = q.get()
        print 'Running %s' % domain
        self.dig(domain)
        q.task_done()
        
    def domainParser(self, i, sema):
        sema.acquire()
        print 'Running %s' % i
        self.dig(i)
        sema.release()