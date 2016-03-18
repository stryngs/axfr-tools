import os

class compare(object):
	''' This class is used for comparisons '''

	def __init__(self):
		pass

	def domains(self):
		''' SQL style Right join comparison
		
		Consider domains previously scanned as table scanned
		Consider list of domains to scan as table todo
		Both tables have a single column, domain
		SELECT t.domain
		FROM scanned S
		RIGHT JOIN todo T
		ON S.domain = T.domain
		WHERE S.domain IS NULL;
		'''		
		## Create the comparisons to prevent re-digging
		oFile = raw_input("List of domains previously scanned?\n")
		nFile = raw_input("List of domains to scan?\n")
		tFile = raw_input("Output File? [nTgts.lst]\n")
		if not tFile:
			tFile = 'nTgts.lst'

		## Create a set of pre-dug
		pSet = set()
		with open(oFile, 'r') as iFile:
			old = iFile.readlines()
			for i in old:
				pSet.add(i.strip())

		## Create a set of new domains
		nSet = set()
		with open(nFile, 'r') as iFile:
			new = iFile.readlines()
			for i in new:
				nSet.add(i.strip())

		## Compare the sets, and remove old from new creating a set of non-dug domains
		with open (tFile, 'w') as oFile:
			for i in nSet - pSet:
				oFile.write(i.strip() + '\n')


	def recurser(self, tDir, d = True, f = True):
		''' This function does a recurse on a given directory, tDir '''
		dList = []
		fList = []
		for dirname, dirnames, filenames in os.walk(tDir):
			if d is True:
				for subdirname in dirnames:
					dList.append(os.path.join(dirname, subdirname))
			else:
				dList = False

			if f is True:
				for filename in filenames:
					fList.append(os.path.join(dirname, filename))
			else:
				fList = False
		return dList, fList
