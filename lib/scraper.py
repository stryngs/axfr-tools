from lxml import html
import os, requests

class scraper(object):
	''' This class is how we scrape '''

	def __init__(self):
		self.nServer = raw_input('Which nameserver to query for?\n')


	def gwebtools(self):
		data = requests.get('http://www.gwebtools.com/ns-spy/%s' % self.nServer)
		tree = html.fromstring(data.content)
		dList = tree.xpath('/html/body/div[2]/div[4]/div/div[1]/form/ul[2]/li/a/text()')

		print ''
		for i in dList:
			print i.lower()

		print ''
		quantity = int(tree.xpath('/html/body/div[2]/div[4]/div/div[1]/form/text()')[9].strip().split(":")[1].strip())
		print 'Total Domains:' + ' ' + str(quantity)

		modCheck = quantity % 25
		if modCheck:
			fUrl = (quantity/25) + 1
		else:
			fUrl = quantity/25
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
				bDir = os.getcwd()
				print '\nWriting %s/domains.lst' % bDir
				with open('domains.lst', 'w') as oFile:
					for i in dList:
						oFile.write(i.lower() + '\n')
					for pages in range(2, fUrl + 1):
						print 'Starting request %s' % pages
						data = requests.get('http://www.gwebtools.com/ns-spy/%s/%s' % (self.nServer, pages))
						tree = html.fromstring(data.content)
						dList = tree.xpath('/html/body/div[2]/div[4]/div/div[1]/form/ul[2]/li/a/text()')
						for i in dList:
							oFile.write(i.lower() + '\n')

				## Declare complete
				print 'Finished!\n'
