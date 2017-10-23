from bs4 import BeautifulSoup
import os, requests

class dScraper(object):
    ''' This class is how we scrape for domains '''

    def __init__(self, dm, api = False):
        self.dm = dm
        self.api = api

    def robtex(self):
        ''' Reverse domain scraper for robtex.com

        Inverted in the sense that this looks for domains which
        use the same nameserver as the given domain
        '''
        dList = []
        sList = []
        bDir = os.getcwd()
        bUrl = 'https://www.robtex.com/en/advisory/dns/'
        dLen = len(self.dm.split('.'))

        ## Split the domain by subs
        for i in range(dLen):
            sList.append(self.dm.split('.')[i])

        ## Reverse the domain for robtex and concatenate
        for i in reversed(sList):
            bUrl = bUrl + i + '/'
        bUrl = bUrl + 'shared.html'

        ## Grab data and soup it up
        data = requests.get(bUrl, headers = {'user-agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(data.content)

        ## Find i tags
        x = soup.find('span', id='shared_pn_mn').parent.parent
        y = x.findAll('i')

        ## Strip i and add to list
        for i in y:
            dList.append(str(i).split('>')[1].split('<')[0])

        ## Finalize list
        if not self.api:
            mode = 'w'
        else:
            mode = 'a'
        with open('domains.lst', mode) as oFile:
            if not self.api:
                print '\nWriting %s/domains.lst' % bDir
            else:
                print '\nWriting %s/domains.lst - (%s)' % (bDir, self.dm)
            for i in dList:
                oFile.write(i + '\n')
        print 'Finished!\n'