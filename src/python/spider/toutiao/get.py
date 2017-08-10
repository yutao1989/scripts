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
import db_dump

socket.setdefaulttimeout(3)
url_temp = "https://s3.ap-northeast-1.amazonaws.com/spring-s3/%s"
bucket_name = "spring-s3"

bucket = None

def imge_transfer(url,surl):
    # post url to image downloader
    pts = url.split("?")[0].strip("/").split("/")
    name = "spider/%s" % "/".join(pts[2:])
    nsrc = url_temp % name
    util.log_msg("image_process\t%s\t%s\t%s" % (url,name,surl))
    return (url,"/%s/%s" % (bucket_name,name),nsrc)

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
            src = util.parse_url(referer,node.get(key))
            if src.find("?") > -1:
                # not good here
                util.log_msg("expecting image url with no params%s" % src)
                continue
            _,name,nsrc = imge_transfer(src,referer)
            node.set(key,nsrc)
            imgs.append((src,name))
    target = "".join([etree.tounicode(node) for node in tree.xpath("/html/body/*")])
    imgs_str = "|".join([o[1] for o in imgs])
    return target,imgs_str

def get_params(p):
    try:
        status,op = subprocess.getstatusoutput("node "+p)
        if status == 0:
            return op
        else:
            return None
    except Exception:
        tp, e,trace = sys.exc_info()
        util.log_msg("execute javascript file error:%s" % str(e))
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
    ourl = "http://www.toutiao.com/c/user/%s/" % u
    url,html = util.get_page({"url":ourl})
    p,h = get_urlinfo(url)
    params = get_params("func.js")
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
                util.log_msg("could not get data from url:%s,data:%s,uid:%s" % (nurl,str(params),u))
                break
            mp = json.loads(html)
            if "data" in mp and isinstance(mp["data"],list):
                if len(mp["data"]) == 0:
                    util.log_msg("no data from response.url:%s" % nurl)
                result = []
                for item in mp["data"]:
                    get_article(util.parse_url(url,item["source_url"]),url,item,fp,result)
                if len(result) > 0:
                    insert_into_db(result)
            else:
                util.log_msg("no data in content.url:%s" % nurl)
            if mp["has_more"]:
                params = get_params("func.js")
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
    else:
        util.log_msg("could parse data from html file,need to check this out.url:%s,referer:%s." % (ourl,referer))

def insert_into_db(mps):
    columns = ['id', 'title', 'source', 'a_type', 'username', 'description', 'content', 'source_url', 'publish_time', 'category', 'tags', 'cover', 'images', 'views', 'comments']
    keys = ['id', 'title', 'from', ('isOriginal',1), 'source', 'abstract', 'content', 'url', 'publishtime', 'category', 'tags', 'cover', 'images', ('views',1), ('comments',1)]
    tt = [("'{%s}'" % o) if isinstance(o,str) else ("{%s}" % o[0]) for o in keys]
    table = "tb_article_crawl"
    c2k_mp = {o[0]:o[1] for o in zip(columns,tt)}
    update_columns = ["views","comments"]
    data = []
    for mp in mps:
        mp["isOriginal"] = 1 if mp["isOriginal"] else 2
        mp["from"] = "今日头条"
        np = {k:(re.sub("[\r\n\t ]+"," ",mp[k]).replace("'","\\'") if isinstance(mp[k],str) else mp[k]) for k in mp.keys()}
        temp_temp = "(%s) %s" % (",".join(tt),  "on duplicate key update "+",".join(["`%s`=%s" % (o,c2k_mp[o]) for o in update_columns]) if len(update_columns)>0 else "")
        try:
            data.append(temp_temp.format_map(np))
        except Exception:
            tp, e,trace = sys.exc_info()
            util.log_msg("format data error:%s" % str(e))
    db_dump.dump_db(table,columns,data)

def get_article(url,referer,data,fp,result2):
    url, h = util.get_page({"url":url,"headers":{"Referer":referer}})
    tree = etree.HTML(h)
    scripts = [o for o in tree.xpath("//script/text()") if o.find("BASE_DATA") > -1 or o.find("__pgcInfo")>-1]
    scripts.append("console.log(JSON.stringify(BASE_DATA))")
    open("data/tmp.js","w").write("\n".join(scripts))
    r = get_params("data/tmp.js")
    if r is not None:
        mp = json.loads(r)
        obj = {"entry":data,"data":mp}
        conf = [("title",["data","artilceInfo","title"]),
                ("content",["data","artilceInfo","content"],None,html.unescape),
                ("comments",["data","commentInfo","comments_count"],0),
                ("isOriginal",["data","artilceInfo","subInfo","isOriginal"],False),
                ("url",["__const",url]),
                ("views",["entry","go_detail_count"], 0),
                ("cover",["entry","image_url"],""),
                ("abstract",["entry","abstract"], ""),
                ("source",["data","artilceInfo","subInfo","source"],""),
                ("publishtime",["data","artilceInfo","subInfo","time"]),
                ("tags",["data","artilceInfo","tagInfo","tags"],"",lambda o:",".join([so["name"] for so in o])),
                ("category",["data","headerInfo","chineseTag"],""),
            ]
        result = {}
        for cf in conf:
            v = util.get_jpath(obj,cf[1],cf[2] if len(cf)>2 else None,cf[3] if len(cf)>3 else None)
            if v is not None:
                result[cf[0]] = v
        result["id"] = hashlib.md5(url.encode("utf-8")).hexdigest()
        if "content" in result:
            result["content"],result["images"] = replace_image(result["content"],url)
            if "cover" in result and len(result["cover"])>0:
                result["cover"] = imge_transfer(util.parse_url(url,result["cover"]),url)[1]
            if len(result) > 0:
                result2.append(result)
        else:
            util.log_msg("could parse content from html file,need to check this out.url:%s,referer:%s." % (url,referer))
    else:
        util.log_msg("could parse data from html file,need to check this out.url:%s,referer:%s." % (url,referer))

def cb(fp):
    #url = "http://www.toutiao.com/"
    #util.get_page({"url":url})
    ids = ["3217488391","3490514559","6952025338","53052328075","62410217001","17742356838","3667603068","6617382708","6474480676","6126424045","6237062541","6613263338","5721425462","3230889860","5460434242","4588938236","4023651976","6675755348","51848596518","3794154752","5766840891","6939911288","53197227173","52231019020","1439117339","3655831911","5963433422","3345437222","3655626426","5963433422","5935444546","6095787239","63826714033","3669967641","4664335991","6960911767","6065077466","5458114046","2921675805","4309017746","3788331986","4143177716","5826315429","52171354099","5446353935","52497881665","3961411576","6303762356","5543282403","3808046799","50099999999"]
    for uid in ids:
        get_user_info(uid,fp)

if "__main__" == __name__:
    fp = open("data/result.txt","a")
    util.manage(cb,(fp,))
