import os
import time

class Dig(object):
    """Wrapper class for the dig-em bash script"""
    
    def singleDig(self, domain):
        os.system('dig-em -d %s pythonS' % domain)
    
    def multiDig(self, domain):
        os.system('dig-em -d %s pythonM' % domain)
