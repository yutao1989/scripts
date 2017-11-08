#! /usr/bin/python3

import util

split_dataurls = lambda o1,o2:([o2],[{"url":o[1],"title":o[0]} for o in o2["urlTitle"]] if "urlTitle" in o2 else [])

sina_entry = {
    "TopNews":("//div[@class=\"top_newslist\"]/ul",[("urlTitle",["mxpath",("./li/a/text()","./li/a/@href")]),("header",["future","Header","name"]),("date",["future","Header","date"])],split_dataurls),
    "Header":("//div[@id=\"wwwidx_imp_con\"]",[("name",["xpath","./div[1]/div/span/a/text()"]),("date",["xpath","./div[1]/span/text()"])])
}

def detect_by_key(name,value):
    return lambda p,cfg,h,entry:True if name in entry and entry[name]==value else False

conf = {
        "www.sina.com.cn":[
            (util.path_detect("/"),sina_entry)
        ],
        "esf.cq.fang.com":[()]
}

if "__main__" == __name__:
    rp = open("data/fang.txt","a")
    seeds = [{"url":"http://esf.cq.fang.com","force":True,"level":1}]
    #seeds = [{"url":"http://www.sina.com.cn","force":True}]
    params = (seeds,conf,rp)
    util.manage(util.schedule,params)
