import os, re, shutil

class Merger(object):
    ''' This class contains methods for merging directories and/or files '''

    def __init__(self):
        pass


    def digs(self, d, f):
        ''' This function merges multiple DIG_INFOs instances '''
        ## Notate the main DIG_INFOs directory
        for i in d:
            if re.search('DIG_INFOs$', i):
                mainDir = i

        ## List out the _ directories
        dList = []
        for i in d:
            if 'DIG_INFOs_' in i:
                dList.append(i)

        ## List out the _ NoNS.lst files along with the main NoNS.lst file
        fList = []
        for i in f:
            if 'DIG_INFOs/NoNS.lst' in i:
                nFile = i
            if re.search('DIG_INFOs_\d+/NoNS\.lst', i):
                fList.append(i)

        ## Concatenante the contents of the _ directories NoNS.lst files into DIG_INFOs/NoNS.lst
        ## Remove the file when complete
        with open(nFile, 'a') as oFile:
            for fName in fList:
                with open(fName) as iFile:
                    for line in iFile:
                        oFile.write(line)
                os.remove(fName)

        ## Move the files from the _ directories to the main DIG_INFOs directory
        for i in dList:
            if re.search('DIG_INFOs_\d+/', i):
                shutil.move(i, mainDir)

        ## Remove _ dirs
        for i in dList:
            if re.search('DIG_INFOs_\d+$', i):
                os.rmdir(i)

        ## Declare complete
        print('Finished!\n')
