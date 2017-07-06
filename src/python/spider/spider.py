#! /usr/bin/python3 -O
#-*- coding=utf-8 -*-

import util
import time
import sys
import re

def split_dataurls(key,mp,datas,urls):
    datas.append((key,mp))
    if "urlTitle" in mp:
        for item in mp["urlTitle"]:
            urls.append({"url":item[1],"title":item[0]})

sina_entry = {
    "TopNews":("//div[@class=\"top_newslist\"]/ul",[("urlTitle",["mxpath",("./li/a/text()","./li/a/@href")]),("header",["future","Header","name"]),("date",["future","Header","date"])],split_dataurls),
    "Header":("//div[@id=\"wwwidx_imp_con\"]",[("name",["xpath","./div[1]/div/span/a/text()"]),("date",["xpath","./div[1]/span/text()"])])
}

conf = {"www.sina.com.cn":[
            (util.path_detect("/"),sina_entry)
        ],
        #"www.facebook.com",("")",
}

def cb():
    '''
    url = "https://www.facebook.com/"
    url,html = util.get_page({"url":url})
    #print(html)
    ##print(type(html))
    open("data/facebook.html","w").write(html)
    #html = open("data/facebook.html").read()
    ts = int(time.time())
    lsd = re.findall("name=\"lsd\" value=\"[^\"]+\"", html)
    lsd = lsd[0].split("\"")[3] if len(lsd) > 0 else None
    lgnrnd = re.findall("name=\"lgnrnd\" value=\"[^\"]+\"",html)
    lgnrnd = lgnrnd[0].split("\"")[3] if len(lgnrnd) > 0 else None
    if lsd is None or lgnrnd is None:
        print("could not parse lsd")
        sys.exit(0)
    data = {
        "lsd":lsd,
        "email":"yutic1989@gmail.com",
        "pass":"!@qwaszx",
        "timezone":-480,
        "lgndim":"eyJ3IjoxOTIwLCJoIjoxMDgwLCJhdyI6MTkyMCwiYWgiOjEwNTMsImMiOjI0fQ==",
        "lgnrnd":lgnrnd,
        "lgnjs":ts,
        "ab_test_data":"AA///AAAAAAAA/A/AAA/AAAAAAAAAAAAAAAAAAAAAAAAf//fA/DBAB",
        "locale":"zh_CN",
        "login_source":"login_bluebar",
        }
    url = "https://www.facebook.com/login.php?login_attempt=1&lwv=110"
    url,html = util.get_page({"url":url,"data":data})
    open("data/facebook2.html","w").write(html)
    '''
    url = "http://www.facebook.com/182826568861663"
    url,html = util.get_page({"url":url})
    open("data/profile.html","w").write(html)

if "__main__" == __name__:
    '''
    seeds = [{"url":"https://www.sina.com.cn"}]
    fp = open("data/result.txt","a")
    params = (seeds,conf,fp)
    util.manage(util.schedule,params)
    '''
    util.manage(cb)

