from urllib import request
from urllib import parse
from http import cookiejar
import time
import socket
import traceback
import chardet
import gzip
import sys
from lxml import etree
import json
import os
import logging
from .template import parse as tparse
from .bloomfilter import bloomfilter

Headers = {
    "Accept-Language":"zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4",
    "Cache-Control":"no-cache",
    "User-Agent":"Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36",
    }
cj = None
bf = None
fname = "data/.cookie"

def parse_url(surl, target, base=None):
    if not surl.startswith('http'):
        return None
    if target.startswith("javascript"):
        return None
    parts = surl.split('/')
    if target.startswith('http'):
        return target
    elif target.startswith('/'):
        return '/'.join(parts[:3])+target
    else:
        if base is not None:
            return base+target
        else:
            return '/'.join(surl.split('/')[:-1])+'/'+target

def log_msg(msg,tp="info"):
    if tp == "info":
        logging.info(msg)
    elif tp == "error":
        logging.error(msg)

def init():
    socket.setdefaulttimeout(5)
    global cj,bf,fname
    logging.basicConfig(level=logging.DEBUG,
        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S',
        filename='./data/p.log',
        filemode='a')
    bf = bloomfilter()
    cj = cookiejar.LWPCookieJar()
    if fname is not None and os.path.exists(fname):
        cj.load(fname)
        
    opener = request.build_opener(request.HTTPCookieProcessor(cj))
    request.install_opener(opener)

def close():
    global cj,bf,fname
    if cj is not None and isinstance(cj,cookiejar.LWPCookieJar):
        cj.save(fname)
    if bf is not None:
        bf.close()

def exists(url):
    global bf
    if bf is None:
        return False
    else:
        return bf.exists(url)

def decode_content(url,html,isgzip=False,encoding=None):
    if isgzip:
            html = gzip.decompress(html)
    if encoding is not None:
        html = html.decode(encoding,"ignore")
    else:
        result = chardet.detect(html)
        if result['encoding'] is None or result["confidence"] < .8:
            log_msg("could not detect content encoding,url:%s" % url,"error")
            html = html.decode("utf-8")
        else:
            html = html.decode(result['encoding'], 'ignore')
    return html

def merge(mp1,mp2,black_list=set(["force"])):
    copy_mp = mp2.copy()
    for key in mp1.keys():
        if key not in copy_mp and key not in black_list:
            copy_mp[key] = mp1[key]
    return copy_mp

def get_header_ignore_case(mp,key):
    for k in mp.keys():
        if k.lower() == key.lower():
            return mp[k].lower()
    return ""
        
def get_page(status):
    st = 2 if "__sleep" not in status or not isinstance(status["__sleep"],int) else status["__sleep"]
    time.sleep(st)
    html = ''
    code = ''
    retry = 4 if "retry" not in status or not isinstance(status["retry"],int) else status["retry"]
    url = status["url"]
    method = "GET" if "method" not in status else status["method"].upper()
    headers = merge(Headers,status["headers"]) if "headers" in status else Headers
    data = status["data"] if "data" in status else None
    if data is not None:
        if type(data) == type({}):
            data = bytes(parse.urlencode(data),"utf-8")
            if method == "GET":
                url = url + "?" + data.decode("utf-8")
                data = None
    response = None
    while True:
        try:
            req = request.Request(url, data, headers,method=method)
            response = request.urlopen(req)
            code = str(response.getcode())
            log_msg('%s\t%s\t%s' % (url, code ,"" if data is None else str(data)))
            assert code[0] == "2"
            html = response.read()
            if "isPic" in status:
                break
            isgzip = True if get_header_ignore_case(response.headers,"Content-Encoding") == "gzip" else False
            content_type = get_header_ignore_case(response.headers,"Content-Type")
            encoding = {o.split(":")[0].strip():o.split(":")[1].strip() for o in content_type.split(";") if o.find(":") > -1}
            if "charset" not in encoding:
                encoding = {o.split("=")[0].strip():o.split("=")[1].strip() for o in content_type.split(";") if o.find("=") > -1}
            encoding = encoding["charset"] if "charset" in encoding else None
            html = decode_content(url,html, isgzip,encoding)
            break
        except Exception:
            tp, e,trace = sys.exc_info()
            log_msg("util.get_page exception:"+str(e))
            if hasattr(e, "getcode") and retry > 0:
                code = str(e.getcode())
                if code[0] in set(["4","5"]):
                    log_msg('%s\t%s\t%s\t%s' % (time.ctime(),url, code ,"" if data is None else str(data)))
                    return (url,"")
            retry -= 1
            if retry <= 0:
                log_msg(('%s\t%s\t%s\t%s\t%s' % (time.ctime(), url, code, str(e), "recovery")),"error")
                log_msg('\t'.join(traceback.format_stack()),"error")
                break
            else:
                time.sleep((6-retry)*5)
    return url,html

def schedule(seeds,conf,data_fp):
    q = []
    global bf
    for seed in seeds:
        q.append(seed)
    while len(q) > 0:
        item = q.pop()
        print(item)
        if "force" not in item and bf.exists(item["url"]):
            continue
        url_parts = item["url"].split("&")[0].strip("/").split("/")
        host = url_parts[2]
        if host in conf:
            nurl,html = get_page(item)
            if nurl != item["url"]:
                url_parts = nurl.split("&")[0].strip("/").split("/")
                host = url_parts[2]
                if host not in conf:
                    continue
            path = "/"+"/".join(url_parts[3:])
            for sconf in conf[host]:
                if sconf[0](path,sconf[1],html,item):
                    datas,urls = tparse(html,sconf[1],item)
                    for data in datas:
                        data_fp.write("%s\t%s\t%s\t%s\n" % (host,path,data[0],json.dumps(data[1])))
                    for url_entry in urls:
                        url_entry["referer"] = nurl
                        if "url" in url_entry:
                            url_entry = merge(item,url_entry)
                            if not url_entry["url"].startswith("http"):
                                turl = parse_url(nurl,url_entry["url"])
                                if turl is not None:
                                    url_entry["url"] = turl
                                    q.append(url_entry)
                            else:
                                q.append(url_entry)

def manage(callback,params=None):
    init()
    callback() if params is None else callback(*params)
    close()
