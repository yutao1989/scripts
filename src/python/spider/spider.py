#! /usr/bin/python3 -O
#-*- coding=utf-8 -*-

import util
import time
import sys
import re
import json

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

def get_info(content,info=None):
    try:
        p = {"collection_token":"","cursor":"","disablepager":False,"overview":False,"profile_id":"100008346345446","pagelet_token":"","tab_key":"friends","lst":"","ftid":None,"order":None,"sk":"friends","importer_state":None}
        loader_info = re.findall('"enableContentLoader"([^\[]+\[[^\]]+){2}',content)
        lst = None
        pglt = None
        if info is None:
            page_token = re.findall('pagelet_token"?:[^\}]+}',content)
            page_token = page_token[0]
            lst = page_token.split("\"")[-2]
            pglt = page_token[page_token.find(":\"")+2:].split("\"")[0]
        else:
            lst = info[0]
            pglt = info[1]
        loader_info = loader_info[0]
        pfx1 = "pagelet_timeline_app_collection_"
        idx1 = loader_info.find(pfx1)
        ct = None
        if idx1 > -1:
            ct = loader_info[idx1+len(pfx1):].split("\"")[0]
        cs = loader_info.split("\"")[-2]
        np = p.copy()
        np["collection_token"] = ct
        np["cursor"] = cs
        np["pagelet_token"] = pglt
        np["lst"] = lst
        np = json.dumps(np)
        return (np,(lst,pglt))
    except Exception:
        tp, e,trace = sys.exc_info()
        util.log_msg("parse paramerter error:"+str(e),"error")
        return (None,None)

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
    #url = "https://www.facebook.com/100008346345446"
    url = "https://www.facebook.com/profile.php?id=100008346345446"
    url,html = util.get_page({"url":url})
    print(url)
    open("data/profile2.html","w").write(html)
    '''

    '''
    c_id = "100014233620831"
    uid = "100008346345446"
    ts = int(time.time())
    url = "https://www.facebook.com/profile.php?id=%s&lst=%s%%3A%s%%3A%d&sk=friends&source_ref=pb_friends_tl" % (uid,c_id,uid,ts)
    url,html = util.get_page({"url":url})
    print(url)
    open("data/friends.html","w").write(html)
    '''
    params = {
        "dpr":"1",
        "__user":"100014233620831",
        "__a":"1",
        "__dyn":"7AgNeyfyGmaxx2u6aEyx91qeCwKAKGgyi8zQC-C267UKewWhE98nwgUy22EaUgxebkwy8xa5WjzEgDKuEjKewExaFQ12VVojxCUSbAWCDxi5-78O5u5o5aayrhVo9ohxGbwYUmC-UjDQ6Evwwh8gUW5oy5EG2ut5xq48a9Ef8Cu4rGUpCzo-8Gm8z8O784afxK9yUvy8lUGdyU4eQEB0",
        "__af":"j0",
        "__req":"26",
        "__be":"-1",
        "__pc":"EXP4:DEFAULT",
        "__rev":"3161010",
        "__spin_r":"3161010",
        "__spin_b":"trunk",
        "__spin_t":"1500360303"
        }
    content = open("data/friends.html").read()
    data,info = get_info(content,None)
    params["data"] = data
    ts = int(time.time())
    params["__spin_t"] = ts
    url = "https://www.facebook.com/ajax/pagelet/generic.php/AllFriendsAppCollectionPagelet"
    url,html = util.get_page({"url":url,"data":params})
    print(url)
    open("data/friends_page.html","w").write(html)

if "__main__" == __name__:
    '''
    seeds = [{"url":"https://www.sina.com.cn"}]
    fp = open("data/result.txt","a")
    params = (seeds,conf,fp)
    util.manage(util.schedule,params)
    '''
    util.manage(cb)

