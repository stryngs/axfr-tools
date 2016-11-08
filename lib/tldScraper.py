from bs4 import BeautifulSoup
from lxml import html
import os, requests, sys

class tScraper(object):
    ''' This class is how we scrape for domains '''

    def __init__(self, tld):
        self.tld = tld


    def domaintyper(self):
        ''' Domain scraper for domaintyper.com

        Rips domains based upon top sites listed
        '''
        ## Create domain list and grab initial info
        self.dList = []
        bUrl = 'https://domaintyper.com/top-websites/most-popular-websites-with-' + self.tld + '-domain/page/'
        page = requests.get(bUrl)
        
        ## Obtain count of domains via BS4
        soup = BeautifulSoup(page.content, 'lxml')
        initRip = soup.find('div', {'class': 'headDescription'})
        finalRip = initRip.find_all('b')
        if len(finalRip) > 1:
            domainCount = str(finalRip[1]).replace('<', '').replace('b', '').replace('/', '').replace('>', '').replace(',', '')
        else:
            domainCount = str(finalRip[0]).replace('<', '').replace('b', '').replace('/', '').replace('>', '').replace(',', '')
        
        
        ## Determine pages and deal with accordingly
        totalPages = int(domainCount) / 100
        finalPage = int(domainCount) % 100
        
        ## Determine total pages
        if finalPage:
            endPage = totalPages + 1
        else:
            endPage = totalPages
        
        ## Get users input for what to do
        print '\nTotal Domains:' + ' ' + domainCount
        print 'Final URL is: %s%s' % (bUrl, endPage)
        uChoice = raw_input('Shall we build the domain list? [y\N]\n')
        if not uChoice or uChoice == 'n'  or uChoice == 'N':
            sys.exit(1)
        else:
            if uChoice == 'y' or uChoice == 'Y':
                partialList = raw_input('\nShall we build a partial list? [y\N]\n')
                if partialList:
                    userPage = int(raw_input('\nEnding URL to build to?\n'))
                    if userPage < endPage:
                        endPage = userPage

        ## Notate contents of first page since it is in memory already
        print 'Starting request %s / %s' % (1, endPage)
        tmpX = soup.find('div', {'class': 'rankTableDiv'})
        tmpY = tmpX.find('tbody')
        tmpZ = tmpY.find_all('tr')
        for i in range(0, len(tmpZ)):
            self.dList.append(str(tmpZ[int(i)]).split('>')[4].split('<')[0])                        

        ## Full download
        if not partialList:

            ## Deal with more than 1 page
            if endPage > 1:
                counter = 2
                for i in range(2, endPage + 1):
                    print 'Starting request %s / %s' % (counter, endPage)
                    page = requests.get(bUrl + str(i))
                    soup = BeautifulSoup(page.content, 'lxml')
                    tmpX = soup.find('div', {'class': 'rankTableDiv'})
                    tmpY = tmpX.find('tbody')
                    tmpZ = tmpY.find_all('tr')
                    for i in range(0, len(tmpZ)):
                        self.dList.append(str(tmpZ[int(i)]).split('>')[4].split('<')[0])
                    counter = counter + 1

            bDir = os.getcwd()
            print '\nWriting %s/domains.lst' % bDir
            lastLine = len(os.linesep)
            with open('domains.lst', 'w') as oFile:
                for i in self.dList:
                    oFile.write(i + '\n')
                oFile.truncate(oFile.tell() - lastLine)

        ## Partial download
        else:
            
            ## Deal with more than 1 page
            if endPage > 1:
                counter = 2
                for i in range(2, endPage + 1):
                    print 'Starting request %s / %s' % (counter, endPage)
                    page = requests.get(bUrl + str(i))
                    soup = BeautifulSoup(page.content, 'lxml')
                    tmpX = soup.find('div', {'class': 'rankTableDiv'})
                    tmpY = tmpX.find('tbody')
                    tmpZ = tmpY.find_all('tr')
                    for i in range(0, len(tmpZ)):
                        self.dList.append(str(tmpZ[int(i)]).split('>')[4].split('<')[0])
                    counter = counter + 1

            bDir = os.getcwd()
            print '\nWriting %s/domains.lst' % bDir
            lastLine = len(os.linesep)
            with open('domains.lst', 'w') as oFile:
                for i in self.dList:
                    oFile.write(i + '\n')
                oFile.truncate(oFile.tell() - lastLine)