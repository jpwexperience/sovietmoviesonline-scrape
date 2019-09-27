#!/usr/bin/python3
#
#Some notes as I go along
#   -Move the csv creation/writing to when the object is made
#   -minimize then number of times you need to iterate through filmInfo
#
import csv
import os, sys, re
import urllib3
import requests

filmInfo = []
baseDir = ""

class filmObj():
    sourceUrl = ""
    downloadUrl = ""
    srtUrl = ""
    title = ""
    year = ""
    director = ""
    domain = ""
    badFile = 0
    badSrt = 0
    fileSize = 0
    srtSize = 0

    def __init__(self, num, fullUrl, baseUrl, name):
        self.num = num
        self.fullUrl = fullUrl
        self.baseUrl = baseUrl
        self.name = name

def downloadFiles(movie):
    global baseDir
    download = movie.downloadUrl
    h = requests.head(movie.downloadUrl, allow_redirects=True)
    header = h.headers
    content_type = header.get('content-type')
    if 'text' in content_type.lower():
        print("Not downloadable")
    elif 'html' in content_type.lower():
        print("Not downloadable")
    else:
        if movie.badFile == 1:
            print("Bad Movie File Set, skipping...")
        else:
            titleNoSpace = movie.title.replace(' ', '_')
            newDir = baseDir + titleNoSpace
            if not os.path.isdir(newDir):
                os.mkdir(newDir)
            print("Downloading: " + movie.downloadUrl)
            r = requests.get(movie.downloadUrl, stream=True)
            with open((newDir + "/" + titleNoSpace  + '.mp4'), 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk) 
            if movie.badSrt == 1:
                print("Bad Srt set, skipping...")
            else:
                r = requests.get(movie.srtUrl, stream=True)
                with open((newDir + "/" + titleNoSpace  + '.srt'), 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk) 


def writeCSV(xmlDir):
    global baseDir
    print(xmlDir)
    newCSV = ""
    base = list(filter(None, re.split('(.*/|\.xml)', xmlDir)))
    print(base)
    if len(base) > 1:
        newCSV = base[0] + base[1] + "-generated.csv"
        baseDir = base[0]
    else:
        newCVS = './' + base[0] + "-generated.csv"
        baseDir = './'
    #print("\n" + baseDir + "\n")
    f = open(newCSV, "w")
    print("New csv file '" + newCSV + "'")
    startLine = "Title|Year|Director|Flick Size (in Gb)|SRT Size (Mb)|Download url|SRT url|Film Info url\n"
    f.write(startLine)
    for i in filmInfo:
        tempFileSize = i.fileSize / 1000000000
        tempSrtSize = i.srtSize / 1000000
        lineWrite = (i.title + "|" 
        + i.year + "|" 
        + i.director + "|" 
        + str(round(tempFileSize, 2)) + "|" 
        + str(round(tempSrtSize, 2)) + "|" 
        + i.downloadUrl + "|" 
        + i.srtUrl +  "|" 
        + i.sourceUrl + "\n")
        f.write(lineWrite)

#takes url and scrapes the proper information from it
def scrapping(movie):
    #print(movie.sourceUrl)
    r = requests.get(movie.sourceUrl)
    if r.status_code == requests.codes.ok:
        movieTitle = re.findall('<td><span>Year:</span>.*</td>|<title>.*</title>|<div class=[\"]director[\"]>.*</a>',r.text)
        #pull movie information from html source
        movieTitle = re.search('<title>.*</title>', r.text)
        movieYear = re.search('<td><span>Year:</span>.*</td>', r.text)
        movieDir = re.search('<div class="director"><a href=".*">[^,]*</a>', r.text)
        if movieDir:
            movieDirSplit = movieDir[0].split(",")
        else:
            movieDirSplit = []
        #print("Title: " + movieTitle[0] + "\n Year: " + movieYear[0] + "\n Director: " + movieDirSplit[0])
        if movieTitle:
            splitTitle = list(filter(None, re.split('<title>|</title>| with.*',movieTitle[0])))
            if len(splitTitle) > 0:
                temp1 = splitTitle[0].replace('&#039;','\'')
                temp2 = temp1.replace('&amp;','&')
                movie.title = temp2
            else:
                print("Something went awry splitting " + movie.name)
        
        #get pertinant year information
        if movieYear:
            splitYear = list(filter(None, re.split('<td>|<span>Year:</span> |</td>',movieYear[0])))
            if len(splitYear) > 0:
                #print(splitYear[0])
                movie.year = splitYear[0]
            else:
                print("Something went awry splitting " + movie.name)
        
        #get pertinant director information
        if movieDirSplit:
            splitDir = list(filter(None, re.split('<div class="director"><a href=[^>]*>|</a>',movieDir[0])))
            if len(splitDir) > 0:
                #print(splitDir[0])
                movie.director = splitDir[0]
            else:
                print("Something went awry splitting " + movie.name)
        
        movie.downloadUrl = movie.domain + "movies/" + movie.num + ".mp4"
        movie.srtUrl = movie.domain + "movies/" + movie.num + ".srt"
        print("\nDownload Url: " + movie.downloadUrl)
        movHead = requests.head(movie.downloadUrl)
        srtHead = requests.head(movie.srtUrl)
        try:
            movie.srtSize = int(srtHead.headers['content-length'])
        except KeyError:
            movie.badSrt = 1
            print("SRT Url Key Error, skipping...")
        try:
            movie.fileSize = int(movHead.headers['content-length'])
        except KeyError:
            movie.badFile = 1
            print("Movie Url KeyError")

        print("Total Size: " + str((movie.fileSize + movie.srtSize) / 1000000000) + " gb")
        #movie.srtSize = int(requests.get(movie.srtUrl, stream=True).headers['Content-length']) / 1000000000
        #print("File Size: " + str(movie.fileSize))
        #print("Download Url: " + movie.downloadUrl + "\n SRT Url: " + movie.srtUrl + "\n")
    else:
        print(movie.sourceUrl + ": Not ok request code")

#Takes in xml file and parses out links and adding their
#respecitve information to a list of filmObj's
def splitting(xmlIn):
    numInfo = []
    f = open(xmlIn, "r")
    for i in f:
        s = i
        xmlSplit = re.split('<url>|</url>|<loc>|</loc>|<lastmod>|</lastmod>',s)
        #print(xmlSplit)        
        xmlValues = list(filter(None, xmlSplit))
        if len(xmlValues) > 1:
            #check if a blog link
            if not re.match(".*/blog/.*|.*/ru/.*", xmlValues[0]):
                #check if movie link
                if re.match(".*/[0-9]*-.*\.html", xmlValues[0]):
                    #split 
                    urlSplit = xmlValues[0].split("/")
                    #print(urlSplit)
                    urlEnd = urlSplit[len(urlSplit) - 1]
                    suffixSplit = urlEnd.split(r'-', 1) 
                    #print(suffixSplit[0])
                    #print(suffixSplit)
                    #check if num has already been added
                    temp = filmObj(suffixSplit[0], 
                                xmlValues[0], 
                                urlEnd, 
                                suffixSplit[len(suffixSplit) - 1])
                    numInfo.append(int(temp.num))
                    filmInfo.append(temp)
    print(numInfo.sort())
                    #htmlPages.append(urlSplit[len(urlSplit) - 1])
                    #list(set(source_list))

def main():
    if len(sys.argv) > 2:
        print("get outta here with all those args")
        exit(1)
    elif len(sys.argv) == 1:
        print("what am I suppose to do with this")
        exit(1)
    #else:
        #print("Good on number of arguments")

    xmlInput = sys.argv[1]
    if not os.path.isfile(xmlInput):
        print("This is not a file")
        exit(1)
    else:
        inSplit = xmlInput.split('.')
        ext = inSplit[len(inSplit) - 1]
        if ext != 'xml':
            print("imma need an xml file chief")
            exit(1)

        #print("That is indeed an existing xml file")
        splitting(xmlInput)
    
    print("--- Scraping Info ---")
    for i in filmInfo:
        #print(i.fullUrl)
        #split the domain name and remove empty values
        domainString = list(filter(None, re.split(r"(.*//[^/]*/)",i.fullUrl)))
        i.domain = domainString[0]
        scrapeUrl = i.domain + "movie/" + i.baseUrl
        #create new movie url for scraping
        if len(domainString) > 0:
            i.sourceUrl = scrapeUrl
            #print(i.sourceUrl)
            scrapping(i)
        else:
            print("Empty url value")
    print("--- Writing CSV File ---")
    writeCSV(sys.argv[1])   
    totalSize = 0
    print("--- Calculating Total Size ---")
    for i in filmInfo:
        totalSize += i.fileSize
        totalSize += i.srtSize
    totalSize = totalSize / 1000000000
    inputString = "\nTotal Download Size: " + str(round(totalSize, 2)) + " gb\nDestination: " + baseDir + "\nWould you like to download [y/n]? "
    downloadChoice = input(inputString) 
    if downloadChoice != 'y':
        print("No Downloads Today")
        exit(1)
    print("--- Downloading Files ---")
    for i in filmInfo:
        downloadFiles(i)

if __name__ == "__main__": 
  
    # calling main function 
    main() 
