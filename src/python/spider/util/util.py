import urllib2
import urllib
import cookielib
import time
import socket
import traceback
import chardet
import StringIO
import gzip
import sys
from lxml import etree
import json
import os
import template

Headers = {
    "Accept-Language":"zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4",
    "Cache-Control":"no-cache",
    "User-Agent":"Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36",
    }
cj = None
logger = None

def print_cookies(cj):
    print("="*20)
    if cj is None:
        return
    cks = cj._cookies
    for key in cks.keys():
        scks = cks[key]
        for skey in scks.keys():
            sscks = scks[skey]
            for sskey in sscks.keys():
                print(key,skey,sskey,sscks[sskey])
    print("="*20)

def load_cookies(fp, cj):
    for line in fp: 
        items = line.strip().split("\t")
        tmp = []
        if len(items) > 3:
            tmp.append(items[0])
            tmp.append(items[1])
            m1 = {"version":"0"}
            m1["path"] = items[3]
            turl = None
            if len(items[2].strip()) > 0:
                items[2] = items[2].strip()
                if items[2][0] == ".":
                    m1["domain"] = items[2]
                    turl = items[2]
                else:
                    turl = "http://"+items[2]
            tmp.append(m1)
            if len(items) > 6 and len(items[6].strip()) > 0:
                tmp.append({"HttpOnly":None})
            else:
                tmp.append({})
            url = None
            if turl[0] == ".":
                url = "http://www"+turl
            elif turl[:4] != "http":
                url = "http://"+turl
            else:
                url = turl
            fake_request = urllib2.Request(url)
            cookie = cj._cookie_from_cookie_tuple(tmp,fake_request)
            cj.set_cookie(cookie)

def save_cookies(cookieMp, fp):
    result = []
    cookies = []
    for key in cookieMp.keys():
        scks = cookieMp[key]
        for skey in scks.keys():
            sscks = scks[skey]
            for sskey in sscks.keys():
                cookies.append(sscks[sskey])
    for cookie in cookies:
        tmp = []
        tmp.append(cookie.name)
        tmp.append(cookie.value)
        tmp.append(cookie.domain)
        tmp.append(cookie.path)
        result.append("\t".join(tmp))
    fp.write("\n".join(result))

class log:
    def __init__(self, info_file=None, error_file=None):
        self.info_stream = open(info_file, 'a') if info_file is not None else sys.stdout
        self.error_stream = self.info_stream if info_file == error_file else (open(error_file, 'a') if error_file is not None else sys.stderr)
        self.count1 = 0
        self.count2 = 0

    def push(self, stream, msg, tp):
        stream.write(('%s\t[%s]\t%s\n' % (tp, time.ctime(), msg)).encode('utf-8'))

    def log_info(self, msg, tp='info'):
        self.push(self.info_stream, msg, tp)
        self.count1 = self.count1 + 1
        if self.count1 > 10:
            self.info_stream.flush()
            self.count1 = 0

    def log_error(self, msg, tp='error'):
        self.push(self.error_stream, msg, tp)
        self.count2 = self.count2 + 1
        if self.count2 > 10:
            self.error_stream.flush()
            self.count2 = 0

    def close(self):
        self.info_stream.close()
        self.error_stream.close()

def log_msg(msg,tp="info"):
    global logger
    if logger is None:
        logger = log("log/log.txt","log/err.txt") if os.path.exists("log") else log()
    if tp == "info":
        logger.log_info(msg)
    elif tp == "error":
        logger.log_error(msg)

def init():
    socket.setdefaulttimeout(5)
    global cj
    cj = cookielib.CookieJar()
    fname = "data/.cookie"
    if os.path.exists("data/.cookie"):
        load_cookies(open(fname),cj)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)

def close():
    global cj,logger
    fname = "data/.cookie"
    if cj is not None:
        save_cookies(cj._cookies,open(fname,"w"))
    if logger is not None:
        logger.close()

def decode_content(html,encoding=None):
    if encoding is not None:
        if encoding.lower().strip() == "gzip":
            tmp = StringIO.StringIO(html)
            gzipper = gzip.GzipFile(fileobj=tmp)
            html = gzipper.read()
            result = chardet.detect(html)
            return  html.decode(result['encoding'], 'ignore')
    result = chardet.detect(html)
    if result['encoding'] is None:
        tmp = StringIO.StringIO(html)
        gzipper = gzip.GzipFile(fileobj=tmp)
        html = gzipper.read()
        result = chardet.detect(html)
        return  html.decode(result['encoding'], 'ignore')
    else:
        return html.decode(result['encoding'], 'ignore')
        
def get_page(status, data=None, headers=None):
    time.sleep(2)
    html = ''
    code = ''
    retry = 4
    url = status["url"]
    if headers is None:
        headers = Headers
    if "referer" in status:
        headers["referer"] = status["referer"]
    if data is not None and type(data) == type({}):
        data = urllib.urlencode(data)
    response = None
    while True:
        try:
            request = urllib2.Request(url, data, headers)
            response = urllib2.urlopen(request)
            code = str(response.getcode())
            log_msg('%s\t%s\t%s' % (url, code ,"" if data is None else str(data)))
            assert code[0] == "2"
            #if code[0] == '2':
            if True:
                html = response.read()
                html = decode_content(html, response.headers.getheader("Content-Encoding"))
            #else:
            #    log_msg("unknown return code:%s,url:%s" % (code,response.geturl()), "error")
            #    html = None
            break
        except Exception,e:
            #tp, e,trace = sys.exc_info()
            #print("<"*30,str(e))
            if hasattr(e, "getcode") and retry > 0:
                code = str(e.getcode())
                #print(code,e.geturl())
                if code[0] == "3":
                    html = e.geturl()
                    headers["referer"] = url
                    url = e.geturl()
                    retry -= 1
                    continue
                elif code[0] in set(["4","5"]):
                    log_msg('%s\t%s\t%s\t%s' % (time.ctime(),url, code ,"" if data is None else str(data)))
                    return (url,None)
            retry -= 1
            if retry > 0:
                log_msg(('%s\t%s\t%s\t%s\t%s' % (time.ctime(), url, code, str(e), "recovery")),"error")
                log_msg('\t'.join(traceback.format_stack()),"error")
                break
            else:
                time.sleep((6-retry)*5)
    return url,html

def schedule(seeds,conf,data_fp):
    q = []
    for seed in seeds:
        q.append(seed)
    while len(q) > 0:
        item = q.pop()
        url_parts = item["url"].split("&")[0].strip("/").split("/")
        host = url_parts[2]
        if host in conf:
            nurl,html = get_page(item,item["data"] if "data" in item else None)
            if nurl != item["url"]:
                url_parts = nurl.split("&")[0].strip("/").split("/")
                host = url_parts[2]
                if host not in conf:
                    continue
            path = "/"+"/".join(url_parts[3:])
            for sconf in conf[host]:
                if sconf[0](path,sconf[1],html):
                    datas,urls = template.parse(html,sconf[1],item)
                    for data in datas:
                        data_fp.write("%s\t%s\t%s\t%s\n" % (host,path,data[0],json.dumps(data[1])))
                    for url_entry in urls:
                        url_entry["referer"] = nurl
                        q.append(url_entry)

def manage(callback,params=None):
    init()
    callback() if params is None else callback(*params)
    close()
