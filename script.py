import json
import re
import urllib.request, urllib.error, urllib.parse
import os, shutil
import urllib.parse

def GetMultipleInput(message,count):
    temp=[]
    for i in range(count):
        temp.append(str(input(message+" "+str(i+1)+" : ")))
    return temp

def ReturnJSONfromURL(URL):
    with urllib.request.urlopen(URL+"/api/json") as url:
        data = json.loads(url.read().decode())
    return data

def Return_SubJobURL_fromJSON(JSON):
    results = []
    try:
        for elem in JSON["subBuilds"]:
            results.append(elem["url"])
    except:
        pass
    return results

def GetHostname(url):
    try:
        hostname = re.match(r'(.*?)/view/', url).group(1)
    except:
        hostname = re.match(r'(.*?)/job/', url).group(1)
    hostname = hostname.replace("http://", "")
    return hostname

def JobNameFromURL(url):
    try:
        JobName = re.findall(r"job/(.*)/",url)
    except:
        JobName = re.findall(r"view/(.*)/",url)
    return JobName[0].split("/", 1)[0]

def urlbuilder(path,hostname):
    if path.startswith('job/'):
        url="http://"+hostname+"/"+path
    return url

def get_links_recursive(base, path, visited,max_depth=10, depth=0):
    hostname = GetHostname(base)
    if depth < max_depth:
        try:
            URLS = Return_SubJobURL_fromJSON(ReturnJSONfromURL(base))

            for link in URLS:
                link=urlbuilder(link, hostname)
                if link not in visited:
                    visited.append(link)
                    #print(f"at depth {depth}: {link}")

                    if link.startswith("http"):
                        get_links_recursive(link, "", visited, max_depth, depth + 1)
                    else:
                        get_links_recursive(base, link, visited, max_depth, depth + 1)
        except:
            print("Excepted in Recursive link generator")
            pass
    return visited

def GetArtifactsRelativeURL(url):
    try:
        JSON=ReturnJSONfromURL(url)
        for i in range(len(JSON["artifacts"])):
            if ".html" in JSON["artifacts"][i]["fileName"]:
                return url+"artifact/"+urllib.parse.quote(JSON["artifacts"][i]["relativePath"])
    except:
        print("Excepted While generating Artifacts")
        return None

def DownloadFileFromURL(url,FailedList,Try=3):
    try:
        reporturl=GetArtifactsRelativeURL(url)
        if reporturl:
            print("Downloading :-",reporturl)
            response = urllib.request.urlopen(reporturl)
            webContent = response.read().decode('UTF-8')

            f = open('reports/'+JobNameFromURL(url)+'.html', 'w')
            f.write(webContent)
            f.close
        else:
            print("Artifacts not returned for :- (debug artifacts relative url)",url)
            FailedList.append(url)
    except:
        print("Failed Downloading File : Try : "+str(4-Try))
        print(url)
        if Try>1:
            DownloadFileFromURL(url,FailedList,Try-1)
        if Try==1:
            FailedList.append(url)

def CleanDirectory(dir):
    for files in os.listdir(dir):
        path = os.path.join(dir, files)
        try:
            shutil.rmtree(path)
        except OSError:
            os.remove(path)
    print("Cleaning Directory Completed")

def main():
    #CountMasters = int(input("Enter No Of Master URL's :- "))
    #MasterURLS = GetMultipleInput("Enter Master URL : ", CountMasters)

    CleanDirectory("reports")

    MasterURLS = os.getenv("InputBuildURLs").splitlines()
    MailID = os.getenv("EmailToSendMail")

    print("Processing below master URL's")
    print(MasterURLS)

    for url in MasterURLS:
        FailedList = []

        print("Crawling Child Jobs....")
        AlljobURLS=get_links_recursive(url, "",[url])

        print("Crawled Child Jobs Are :- \n")
        print(AlljobURLS)

        print("Starting Download.....")
        for alljoburl in AlljobURLS:
            if len(Return_SubJobURL_fromJSON(ReturnJSONfromURL(alljoburl)))==0 and alljoburl!=None:
                DownloadFileFromURL(alljoburl,FailedList)

    if len(FailedList)>0:
        print("Download Failed For Following")
        print(FailedList)
    else:
        print("File Downloaded in the location : ")
    print(shutil.make_archive("archive", 'zip',"reports"))
    print("All Downloaded Reports Archived Successfully")


if __name__ == "__main__":
    main()

