#! /usr/bin/python3

import util
import re

split_dataurls = lambda o1,o2:([o2],[{"url":o[1],"title":o[0]} for o in o2["urlTitle"]] if "urlTitle" in o2 else [])

sina_entry = {
    "TopNews":("//div[@class=\"top_newslist\"]/ul",[("urlTitle",["mxpath",("./li/a/text()","./li/a/@href")]),("header",["future","Header","name"]),("date",["future","Header","date"])],split_dataurls),
    "Header":("//div[@id=\"wwwidx_imp_con\"]",[("name",["xpath","./div[1]/div/span/a/text()"]),("date",["xpath","./div[1]/span/text()"])])
}

def detect_by_key(name,value):
    return lambda p,cfg,h,entry:True if name in entry and entry[name]==value else False

add_level2 = lambda o1,o2:([],[{"name":o[1],"url":o[0],"level":2,"force":True} for o in o2["nameUrl"]])

esf_l1_entry = {
    "District":(
        "//div[@id=\"list_D02_10\"]",
        [
            ("nameUrl",["xpath_lambda","./div[@class=\"qxName\"]/a[@href]",lambda o,info:(util.parse_url(info["url"],o.get("href")),o.text.strip())])
        ],
        add_level2
    ),
}

add_level3 = lambda o1,o2:([],[{"name":o[1],"url":o[0],"level":3,"force":True,"path":o2["source"]} for o in (o2["nameUrl"] if isinstance(o2["nameUrl"],list) and not isinstance(o2["nameUrl"][0],str) else [o2["nameUrl"]])])

esf_l2_entry = {
    "District":(
        "//div[@id=\"div_shangQuan\"]",
        [
            ("nameUrl",["xpath_lambda",".//p[@id=\"shangQuancontain\"]/a[@href]",lambda o,info:(util.parse_url(info["url"],o.get("href")),o.text.strip()) if o.text.strip()!="不限" else None]),
            ("source",["jpath",["entrance","name"]])
        ],
        add_level3
    ),
}

all_text = lambda o,info:re.sub("\s+"," "," ".join(o.itertext())).strip()

esf_l3_entry = {
    "Item":(
        '//div[@class="houseList"]/dl',
        [
            ("image",["xpath","./dt//img/@src"]),
            ("title",["xpath_lambda","./dd/p[@class=\"title\"]",all_text]),
            ("url",["xpath","./dd/p[@class=\"title\"]/a/@href"]),
            ("descript",["xpath_lambda","./dd/p[@class=\"mt12\"]",all_text]),
            ("brand_name",["xpath","./dd/p[@class=\"mt10\"]/a/@title"]),
            ("brand_url",["xpath","./dd/p[@class=\"mt10\"]/a/@href"]),
            ("addr",["xpath","./dd/p[@class=\"mt10\"]/span/@title"]),
            ("size",["xpath_lambda", "./dd/div[@class]",lambda o,info:all_text(o,info) if o.get("class").find("area")>-1 else None]),
            ("price_total",["xpath_lambda","./dd/div[@class=\"moreInfo\"]/p[1]",all_text]),
            ("price_per_squaremeter",["xpath_lambda","./dd/div[@class=\"moreInfo\"]/p[2]",all_text])
        ]
    )
}

sina_news_entry = {
    "HeadNews":(
        '//div[@id="syncad_1"]/h1[@data-client="headline"]/a',
        [
            ("title",["xpath","./text()"]),
            ("url",["xpath","./@href"])
        ]
    ),
    "ImportNews":(
        '//div[@id="ad_entry_b2"]/ul/li/a',
        [
            ("title",["xpath","./text()"]),
            ("url",["xpath","./@href"])
        ]
    ),
    "DomesticNews":(
        '//div[@id="blk_new_gnxw"]//ul/li/a',
        [
            ("title",["xpath","./text()"]),
            ("url",["xpath","./@href"])
        ]
    ),
    "LocalNews":(
        '//div[@id="blk_new_bdxw"]//ul/li/a',
        [
            ("title",["xpath","./text()"]),
            ("url",["xpath","./@href"])
        ]
    ),
    "GangTaiNews":(
        '//div[@id="blk_new_gtxw"]//ul/li/a',
        [
            ("title",["xpath","./text()"]),
            ("url",["xpath","./@href"])
        ]
    ),
    "InternationalNews":(
        '//div[@id="blk_gjxw_01"]//ul/li/a',
        [
            ("title",["xpath","./text()"]),
            ("url",["xpath","./@href"])
        ]
    ),
    "Finance_Tech_News":(
        '//div[@id="blk_cjkjqcfc_01"]//ul/li/a',
        [
            ("title",["xpath","./text()"]),
            ("url",["xpath","./@href"])
        ]
    ),
    "Sport_Entertain_News":(
        '//div[@id="blk_lctycp_01"]//ul/li/a',
        [
            ("title",["xpath","./text()"]),
            ("url",["xpath","./@href"])
        ]
    ),
    "Social_News":(
        '//div[@id="blk_sh_01"]//ul/li/a',
        [
            ("title",["xpath","./text()"]),
            ("url",["xpath","./@href"])
        ]
    )
}

conf = {
        "www.sina.com.cn":[
            (util.path_detect("/"),sina_entry)
        ],
        "esf.cq.fang.com":[
            (detect_by_key("level",1),esf_l1_entry),
            (detect_by_key("level",2),esf_l2_entry),
            (detect_by_key("level",3),esf_l3_entry),
        ],
        "news.sina.com.cn":[
            (util.path_detect("/"),sina_news_entry)
        ]
}

if "__main__" == __name__:
    #rp = open("data/fang2.txt","a")
    rp = open("data/sina_news.txt","a")
    #seeds = [{"url":"http://esf.cq.fang.com","force":True,"level":1}]
    #seeds = [{"url":"http://www.sina.com.cn","force":True}]
    #seeds = [{"url":"http://esf.cq.fang.com/house-a059-b05533/","force":True,"level":3}]
    seeds = [{"url":"http://news.sina.com.cn/","force":True,"__sleep":1}]
    params = (seeds,conf,rp)
    util.manage(util.schedule,params)
