#! /usr/bin/python3

import sys
sys.path.insert(0,"/home/yutao/job/spring/spring3/spider_usual/")
import util
import json
import time
import subprocess
from lxml import etree
import re
import html
import boto3
import socket
import hashlib

socket.setdefaulttimeout(3)
url_temp = "https://s3.ap-northeast-1.amazonaws.com/spring-s3/%s"
bucket_name = "spring-s3"

bucket = None

def imge_transfer(url):
    pts = url.split("?")[0].strip("/").split("/")
    name = "spider/%s" % "/".join(pts[2:])
    nsrc = url_temp % name
    return (url,name,nsrc)

def put_s3(data,key):
    global bucket
    retry = 1
    while True:
        try:
            if bucket is None:
                s3 = boto3.resource("s3")
                bucket = s3.Bucket(bucket_name)
            bucket.put_object(Key=key, Body=data)
            break
        except Exception:
            tp, e,trace = sys.exc_info()
            bucket = None
            retry -= 1
            if retry <= 0:
                print("could not upload!!",e)
                break

def replace_image(content,referer):
    tree = etree.HTML(content)
    nodes = tree.xpath("//img")
    imgs = []
    for node in nodes:
        keys = node.keys()
        key = "src" if "src" in keys else ("href" if "href" in keys else None)
        if key is not None:
            src = node.get(key)
            if src.find("?") > -1:
                # not good here
                continue
            _,name,nsrc = imge_transfer(src)
            node.set(key,nsrc)
            imgs.append((src,name))
    target = "".join([etree.tounicode(node) for node in tree.xpath("/html/body/*")])
    imgs_str = "|".join(["/%s/%s" % (bucket_name,o[1]) for o in imgs])
    return target,imgs_str


def get_params(p=None):
    try:
        if p is not None:
            status,op = subprocess.getstatusoutput("node "+p)
        else:
            status,op = subprocess.getstatusoutput("node func.js")
        if status == 0:
            return op
        else:
            return None
    except Exception:
        tp, e,trace = sys.exc_info()
        print(e)
        return None

def get_userinfo(html):
    tree = etree.HTML(html)
    ids = [re.findall("id: ?[\d]+",o[j:j+200]) for o in tree.xpath("//script/text()") for j in [o.find("var userInfo")] if j > -1]
    if len(ids) > 0 and len(ids[0]) > 0:
        return ids[0][0].split(":")[-1].strip()
    else:
        return None

def get_urlinfo(url):
    pts = url.strip("/ \t").split("/")
    if len(pts) > 2:
        return pts[0],pts[2]
    else:
        return None,None

def get_user_info(u,fp):
    #url = "http://www.toutiao.com/"
    #util.get_page({"url":url})
    url = "http://www.toutiao.com/c/user/%s/" % u
    url,html = util.get_page({"url":url})
    p,h = get_urlinfo(url)
    params = get_params()
    uid = get_userinfo(html)
    if params is not None and uid is not None:
        params = json.loads(params)
        params["user_id"] = uid
        path = "/c/user/article/"
        nurl = "%s//%s%s" % (p,h,path)
        count = 1
        while True:
            url,html = util.get_page({"url":nurl,"data":params,"method":"post"})
            if html is None or len(html) == 0:
                break
            mp = json.loads(html)
            if "data" in mp and isinstance(mp["data"],list):
                for item in mp["data"]:
                    #fp.write("%s\t%s\n" % (uid,json.dumps(item)))
                    get_article(util.parse_url(url,item["source_url"]),url,item,fp)
                    break
            if mp["has_more"]:
                params = get_params()
                params = json.loads(params)
                params["user_id"] = uid
                nxt = mp["next"]
                for key in nxt.keys():
                    params[key]=nxt[key]
            else:
                break
            count -= 1
            if count <= 0:
                break

def get_article(url,referer,data,fp):
    url, h = util.get_page({"url":url,"headers":{"Referer":referer}})
    #open("data/article.html","w").write(h)
    #h = open("data/article.html").read()
    tree = etree.HTML(h)
    scripts = [o for o in tree.xpath("//script/text()") if o.find("BASE_DATA") > -1 or o.find("__pgcInfo")>-1]
    scripts.append("console.log(JSON.stringify(BASE_DATA))")
    open("data/tmp.js","w").write("\n".join(scripts))
    r = get_params("data/tmp.js")
    if r is not None:
        mp = json.loads(r)
        obj = {"entry":data,"data":mp}
        conf = [("title",["data","artilceInfo","title"]),
                ("content",["data","artilceInfo","content"],html.unescape),
                ("comments",["data","commentInfo","comments_count"]),
                ("isOriginal",["data","artilceInfo","subInfo","isOriginal"]),
                ("url",["__const",url]),
                ("views",["entry","go_detail_count"]),
                ("cover",["entry","image_url"]),
                ("abstract",["entry","abstract"]),
                ("source",["data","artilceInfo","subInfo","source"]),
                ("publishtime",["data","artilceInfo","subInfo","time"]),
                ("tags",["data","artilceInfo","tagInfo","tags"],lambda o:",".join([so["name"] for so in o])),
                ("category",["data","headerInfo","chineseTag"]),
            ]
        result = {}
        for cf in conf:
            v = util.get_jpath(obj,cf[1],p=cf[2] if len(cf)>2 else None)
            if v is not None:
                result[cf[0]] = v
        result["id"] = hashlib.md5(url.encode("utf-8")).hexdigest()
        if "content" in result:
            result["content"],result["images"] = replace_image(result["content"],url)
            if "cover" in result and len(result["cover"])>0:
                result["cover"] = imge_transfer(result["cover"])[2]
            #result["isOriginal"] = 
        if len(result) > 0 and "source" in result:
            fp.write("%s\t%s\t%s\n" % (result["source"],result["publishtime"],json.dumps(result)))

def cb(fp):
    get_user_info("6503227857",fp)
    #url = "http://www.toutiao.com/item/6451438046603641357/"
    #get_article(url,url,{},fp)

if "__main__" == __name__:
    fp = open("data/result.txt","a")
    util.manage(cb,(fp,))
