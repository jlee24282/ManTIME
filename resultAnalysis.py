
import glob
import re
import os

def outputDataAnal():
    docCount = 0

    #cumulative
    cEvent = 0
    cTime3 = 0

    #cumulative each type
    cEventAll = {}
    cTime3All = {}


    outputf = open('resultAnalysis/resultManTIME.txt',  "a")
    errorFiles = open('resultAnalysis/resultManTIME_parseErrors.txt', "a")
    for file in glob.glob("output/*"):
        if os.stat(file).st_size == 0:
            errorFiles.write(str(file) + '\n')
        else:
            with open(file) as f:
                article = f.readlines()
                docCount = docCount+1
                #Event

                cEvent  = cEvent +  len(str(article).split("</EVENT>"))-1
                for type in re.findall (' class=\"(.*?)\">', str(article), re.DOTALL):
                    if type in cEventAll.keys():
                        cEventAll[type] = cEventAll[type] + 1
                    else:
                        cEventAll[type] = 1

                #Time
                cTime3 = cTime3 + len(str(article).split("</TIMEX3>"))-1
                #print re.findall (' type=\"(.*?)\" value=', str(article), re.DOTALL)
                for classes in re.findall (' type=\"(.*?)\" value=', str(article), re.DOTALL):
                    if classes in cTime3All.keys():
                        cTime3All[classes] = cTime3All[classes] +1
                    else:
                        cTime3All[classes] = 1

                #write results for time

                f.close()
    #Average Data Per Document
    outputf.write('######################################################################\n')
    avEvent = float(cEvent) / float(docCount)
    print cEvent
    print docCount
    avTime3 = float(cTime3) / float(docCount)
    avEventT = {}
    avTime3T = {}

    for key, item in cEventAll.iteritems():
        if key not in avEventT.keys():
            avEventT[key] = item/docCount

    for key, item in cTime3All.iteritems():
        if key not in avTime3T.keys():
            avTime3T[key] = float(item)/float(docCount)
    outputf.write('Total Documents: ' + str(docCount) + '\n')
    outputf.write('Average EVENT Occurence per Document: ' + str(avEvent) + '\n')
    outputf.write('Average TIME Occurence per Document: ' + str(avTime3)+ '\n')
    outputf.write('Average Event Type Occurence Per Document' + str(avEventT)+ '\n')
    outputf.write('Average TIME Type Occurence Per Document' + str(avTime3T)+ '\n')
    ######################################################################
    outputf.write('######################################################################'+ '\n')
    #Average Data cumulative
    outputf.write('TOTAL EVENT: ' + str(cEvent)+ '\n')
    outputf.write('TOTAL TIME: ' + str(cTime3)+ '\n')
    outputf.write('TOTAL EVENT type occurence (Cumulative): ' + str(cEventAll)+ '\n')
    outputf.write('TOTAL TIME type occurence (Cumulative: ' + str(cTime3All)+ '\n')
    outputf.write('######################################################################'+ '\n')
    outputf.close()
    errorFiles.close()

def main():
    outputDataAnal()


if __name__ == '__main__':
    main()
