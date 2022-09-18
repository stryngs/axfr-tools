import os
import time

class Dig(object):
    """Wrapper class for the dig-em bash script"""

    def __init__(self):
        self.counter = 0


    def singleDig(self, domain):
        os.system(f'dig-em -d {domain} pythonS')


    def multiDig(self, domain):
        os.system(f'dig-em -d {domain} pythonM')
