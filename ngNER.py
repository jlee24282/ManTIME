
import json
import glob
import csv
import dicttoxml

def jsonToData():
    # Attributes
    rawDataAll = []
    flag24 = False
    flag22 = False
    flag23 = False
    flag21 = False
    lenList = []
    # get files that contains string BringBackOurGIrls2
    for files in glob.glob("test/samples/data*"):
        f = open(files, 'r')
        lines = f.readlines()

        for line in lines:
            jline = json.loads(line)
            rawDataAll.append(jline)
            #print len(jline.keys())
            lenList.append(len(jline.keys()))
        f.close()
    print 'total' + str(len(lenList))
    print max(lenList)
    print min(lenList)
    # All out
    #printData(rawDataAll)
    return rawDataAll

def jsonToTml():
    # Attributes
    rawDataAll = []
    lenList = []
    # get files that contains string BringBackOurGIrls2
    for files in glob.glob("test/samples/data*"):
        f = open(files, 'r')
        lines = f.readlines()

        for line in lines:
            jline = json.loads(line)
            rawDataAll.append(jline)
            lenList.append(len(jline.keys()))
        f.close()
    # All out
    return rawDataAll

def json2xml(json_obj, line_padding="\n"):
    result_list = list()

    json_obj_type = type(json_obj)

    if json_obj_type is list:
        for sub_elem in json_obj:
            result_list.append(json2xml(sub_elem, line_padding))

        return "\n".join(result_list)

    if json_obj_type is dict:
        for tag_name in json_obj:
            sub_obj = json_obj[tag_name]
            result_list.append("%s<%s>" % (line_padding, tag_name))
            result_list.append(json2xml(sub_obj, "\t" + line_padding))
            result_list.append("%s</%s>" % (line_padding, tag_name))
        return "\n".join(result_list)

    return "%s%s" % (line_padding, json_obj)

def main():
    """
    string = '{"tags":[],"publishingPlatform":{}}'
    jline = json.loads(string)
    xml = json2xml(jline, '\n')
    print xml
    """
    for files in glob.glob("test/samples/data*"):
        f = open(files, 'r')
        lines = f.readlines()
        rawDataAll = []
        inFileName = files.replace('test/samples/', '')
        print inFileName
        jNum = 0
        for line in lines:
            jline = json.loads(line)

            # extract only sequenceID, title, topics, estimatedPublishedDate, content
            sequenceID_tmp = jline['sequenceId']
            title_tmp = jline['title']
            topics_tmp = jline['topics']
            estimatedPublishedDate_tmp = jline['estimatedPublishedDate']
            content_tmp = jline['content']
            # jline.clear()
            # jline['TEXT'] = content_tmp
            # jline['TITLE'] = title_tmp
            # jline['DCT'] = estimatedPublishedDate_tmp
            # jline['DOCID'] = sequenceID_tmp
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            print estimatedPublishedDate_tmp[0:10]
            readfile = ""

            with open("/Users/JLee/PycharmProjects/ManTIME/test/template.tml") as f:
                readfile = "".join(f.readlines())
                print sequenceID_tmp
                readfile = readfile.replace("#id", sequenceID_tmp)
                readfile = readfile.replace("#title", title_tmp)
                readfile = readfile.replace("#text", content_tmp)
                readfile = readfile.replace("2013-03-22", estimatedPublishedDate_tmp[0:10])
                date = str(estimatedPublishedDate_tmp[0:10])
                month = months[int(float(str(estimatedPublishedDate_tmp[0:10]).split("-")[1]))-1]
                readfile = readfile.replace("March 22, 2013", month+" "+date.split("-")[2] + ", " + date.split("-")[0])

            outFile = inFileName.replace('.txt', '_'+str(jNum)+'.tml')
            # print outFile
            jNum = jNum + 1
            outfile = open('test/'+outFile, 'w')
            # readfile = readfile.replace(u"\u2018", "'").replace(u"\u2019", "'").replace(u'\xa0', u' ').replace(u'\u201c', u'')


            udata = readfile.encode("ascii", "ignore")

            outfile.write(udata)
            outfile.close()







            #jline['TOPICS'] = topics_tmp

            #print jline
            # articleInfo = jline
            # xml = dicttoxml.dicttoxml(articleInfo).replace('root', 'TimeML')
            # xml = xml.replace('><', '> \n<')
            # xml = xml.replace('</TIMEX> \n<', '><').replace(' \n<TIMEX', '<TIMEX').replace('></DCT>', '</DCT>')
            # xml = xml.replace('<TIMEX type="str">', '<TIMEX type="DATE" temporalFunction="false" functionInDocument="CREATION_TIME">')
            # outFile = inFileName.replace('.txt', '_'+str(jNum)+'.tml')
            # # print outFile
            # jNum = jNum + 1
            # outfile = open('test/'+outFile, 'w')
            # outfile.write(xml)
            # outfile.close()
        f.close()


if __name__ == '__main__':
    main()