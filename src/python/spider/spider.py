#! /usr/bin/python -O
#-*- coding=utf-8 -*-

import util

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
        ]
}

if "__main__" == __name__:
    seeds = [{"url":"http://www.sina.com.cn"}]
    fp = open("data/result.txt","a")
    params = (seeds,conf,fp)
    util.manage(util.schedule,params)
