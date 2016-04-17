from lxml import html
import os, requests

class nScraper(object):
    ''' This class is how we reverse scrape nameservers'''

    def __init__(self, nServer, api = False):
        self.nServer = nServer
        self.api = api


    def gwebtools(self):
        ''' Reverse domain scraper for gwebtools.com '''
        bDir = os.getcwd()
        if not self.api:
            mode = 'w'
        else:
            mode = 'a'
        data = requests.get('http://www.gwebtools.com/ns-spy/%s' % self.nServer)
        tree = html.fromstring(data.content)
        dList = tree.xpath('/html/body/div[2]/div[4]/div/div[1]/form/ul[2]/li/a/text()')
        quantity = int(tree.xpath('/html/body/div[2]/div[4]/div/div[1]/form/text()')[9].strip().split(":")[1].strip())
        modCheck = quantity % 25
        if modCheck:
            fUrl = (quantity/25) + 1
        else:
            fUrl = quantity/25

        if not self.api:
            print ''
            for i in dList:
                print i.lower()
            print '\nTotal Domains:' + ' ' + str(quantity)
            print 'Final URL is: http://www.gwebtools.com/ns-spy/%s/%s' % (self.nServer, str(fUrl))
            bList = raw_input('Shall we build the domain list? [y\N]\n')
            if not bList or bList == 'n'  or bList == 'N':
                exit(1)
            else:
                if bList == 'y' or bList == 'Y':
                    fList = raw_input('\nShall we build a partial list? [y\N]\n')
                    if fList:
                        fUrl = raw_input('\nEnding URL to build to?\n')
                        fUrl = int(fUrl)

        if not self.api:
            print '\nWriting %s/domains.lst' % bDir
        else:
            print '\nWriting %s/domains.lst - (%s)' % (bDir, self.nServer)
        with open('domains.lst', mode) as oFile:
            for i in dList:
                oFile.write(i.lower() + '\n')
            for pages in range(2, fUrl + 1):
                if not self.api:
                    print 'Starting request %s' % pages
                else:
                    print 'Starting request %s (%s - %s)' % (pages, self.nServer, fUrl)
                data = requests.get('http://www.gwebtools.com/ns-spy/%s/%s' % (self.nServer, pages))
                tree = html.fromstring(data.content)
                dList = tree.xpath('/html/body/div[2]/div[4]/div/div[1]/form/ul[2]/li/a/text()')
                for i in dList:
                    oFile.write(i.lower() + '\n')
        print 'Finished!\n'


    def whois(self):
        ''' Reverse domain scraper for who.is '''
        print ''
        bDir = os.getcwd()
        bUrl = 'http://who.is/nameserver/'
        nSvr = self.nServer
        pCount = 1
        pMax = 11
        tDomains = 0
        if not self.api:
            mode = 'w'
        else:
            mode = 'a'

        ## Open the file for writing
        with open('domains.lst', mode) as oFile:
            if not self.api:
                print '\nWriting %s/domains.lst' % bDir
            else:
                print '\nWriting %s/domains.lst - (%s)' % (bDir, self.nServer)

            def uGrab(uList):
                ''' This sub-function grabs the domains from who.is '''
                uCount = 1
                while uCount < uLen:
                    uDst = '/html/body/div/div/div/div[2]/div/div/div[3]/table/tbody/tr[%s]/td[1]/a/text()' % uCount
                    lStrip = tree.xpath(uDst)
                    uList.append(lStrip[0])
                    uCount += 1

            ## The max page count for who.is, will always be 10
            while pCount < 11:
                uList = []
                fUrl = '%s/%s/%s' % (bUrl, nSvr, pCount)
                data = requests.get(fUrl, headers = {'user-agent': 'Mozilla/5.0'})
                tree = html.fromstring(data.content)
                uLen = len(tree.xpath('/html/body/div/div/div/div[2]/div/div/div[3]/table/tbody/text()'))
                uGrab(uList)
                if not self.api:
                    print 'Starting request %s' % pCount
                else:
                    print 'Starting request %s (%s)' % (pCount, self.nServer)
                cDomains = len(uList)
                print 'Collected domains: %s' % cDomains
                tDomains = cDomains + tDomains
                print 'Total domains: %s\n' % tDomains
                for i in uList:
                    oFile.write(i.lower() + '\n')
                pCount += 1
                if uLen < 20:
                    break
            print 'Finished !\n'
