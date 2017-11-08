#! /usr/bin/python3

import sys
sys.path.insert(0,"/home/yutao/git/scripts/src/python/spider")
import util
from lxml import etree
import json
import re
import fmt_json

def get(url,fname):
    url,html = util.get_page({"url":url})
    open(fname,"w").write(html)

def get_entry(html):
    tree = etree.HTML(html)
    return [(o.get("href"),o.text) for o in tree.xpath("//div[@id=\"list_D02_10\"]/div/a")]

def get_sub(html):
    tree = etree.HTML(html)
    return [(o.get("href"),o.text) for o in tree.xpath("//div[@id=\"div_shangQuan\"]//a")]

all_text_lbd = lambda o,info:re.sub("[ \t\n\r]+"," ","".join(o.itertext())).strip()
url_parse_lbd = lambda o,info:util.parse_url(info["url"],o)

list_mp = {
        "cover":"./dt/a/img/@src",
        "url":("./dt/a/@href",url_parse_lbd),
        "title":"./dd/p[@class=\"title\"]/a/@title",
        "info":("./dd/p[@class=\"mt12\"]",all_text_lbd),
        "brand":"./dd/p[@class=\"mt10\"]/a/@title",
        "brand_url":("./dd/p[@class=\"mt10\"]/a/@href", url_parse_lbd),
        "addr":"./dd/p[@class=\"mt10\"]/span/@title",
        "tags":"./dd//div[@class=\"pt4 floatl\"]/span/text()",
        "price":("./dd/div[@class=\"moreInfo\"]/p[1]",all_text_lbd),
        "average_price":("./dd/div[@class=\"moreInfo\"]/p[2]",all_text_lbd),
        "size":("./dd/div[@class=\"area alignR\"]/p[1]/text()",lambda o,info:o[:-1]),
    }

def get_comm(nodes,cfg,info):
    lst = []
    for node in nodes:
        result = {}
        for k in cfg:
            v = cfg[k]
            ns = None
            if isinstance(v,tuple):
                ns = [o1[0] if (isinstance(o1,list) or isinstance(o1,tuple)) and len(o1)==1 else o1 for o in node.xpath(v[0]) for o1 in [v[1](o,info)] if o1 is not None and len(o1)>0]
            else:
                ns = node.xpath(v)
            if len(ns) == 1:
                result[k] = re.sub("[\t\r\n ]+"," ",ns[0]).strip() if isinstance(ns[0],str) else ns[0]
            elif len(ns)>1:
                result[k] = [re.sub("[\t\r\n ]+"," ",o).strip() if isinstance(o,str) else o for o in ns if o is not None]
        if len(result) > 0:
            lst.append(result)
    return lst

def get_list(html,url):
    tree = etree.HTML(html)
    info = {"url":url}
    nodes = tree.xpath("//div[@name=\"div_houselist\"]/dl")
    data = get_comm(nodes,list_mp,info)
    nodes = tree.xpath("//a[@id=\"PageControl1_hlk_next\"]/@href")
    next_url = util.parse_url(url,nodes[0]) if len(nodes)==1 and nodes[0].strip() != "" else None
    return next_url,data

dtl_mp = {
        "title":".//div[@id=\"lpname\"]/text()",
        "img_title":(".//div[@id=\"bigImgBox\"]/div/img",lambda o,info:[[o.get("src"),o.get("imagetypename") if "imagetypename" in o1 else ""] if "src" in o1 else None for o1 in [o.keys()]][0]),
        "price":(".//div[@class=\"tab-cont-right\"]/div[2]/div[1]",all_text_lbd),
        "first_term_loan":(".//div[@class=\"shoufu_tan\"]",all_text_lbd),
        "info":('.//div[@class="tab-cont-right"]/div/div[@class="trl-item1"]',lambda o,info:[(o1[0].text.strip(),o1[1].text.strip()) if len(o1)==2 else None for o1 in [o.getchildren()]][0]),
        "brand":".//a[@id=\"agantesfxq_C03_05\"]/text()",
        "manager":(".//div[@class=\"trlcont\"]",lambda o,info:[all_text_lbd(o1,info) for o1 in o.getchildren() if "class" in o1.keys() and o1.get("class").find("trlcont-line")>-1]),
        "detail":(".//div[@class=\"content-item\"]//div", lambda o,info:[o3 if "" not in o3 else None for o1 in [o] if "class" in o1.keys() and o1.get("class").find("text-item")>-1 for o2 in [o1.getchildren()] if len(o2)==2 for o3 in [(all_text_lbd(o2[0],info),all_text_lbd(o2[1],info))]]),
        "descript":(".//div[@class=\"content-item\"]",lambda o,info:all_text_lbd(o,info) if len([o1 for o1 in [o.getchildren()] if len(o1)>0 and "class" in o1[0].keys() and o1[0].get("class")=="title" and "".join(o1[0].itertext()).find("房源描述")>-1])>0 else None)
    }

def get_detail(html,url):
    tree = etree.HTML(html)
    info = {"url":url}
    nodes = tree.xpath("/html")
    return get_comm(nodes,dtl_mp,info)

def pagelet(url,fp,context):
    fp.write()

def cb():
    url = "http://esf.cq.fang.com"
    #url,html = util.get_page({"url":url})
    html = open("data/esf.html").read()
    entries = get_entry(html)
    fp = open("data/result.txt","a")
    for entry in entries:
        if entry[0] is None:
            continue
        eurl = util.parse_url(url,entry[0])
        html = open("data/yubei.html").read()
        eurl,html = util.get_page()
        subs = get_sub(html)
        for sub in subs:
            surl = util.parse_url(eurl,sub[0])
            if surl == eurl:
                continue
            html = open("data/list.html").read()
            nurl,items = get_list(html,surl)
    fp.close()

def test():
    '''
    html = open("data/esf.html").read()
    print(get_entry(html))
    html = open("data/yubei.html").read()
    print(get_sub(html))
    url = "http://esf.cq.fang.com/house-a058-b019985/"
    url = "http://esf.cq.fang.com/chushou/3_171310154.htm"
    fname = "data/detail.html"
    get(url,fname)
    url = "http://esf.cq.fang.com/house-a058-b019985/"
    fname = "data/list.html"
    html = open(fname).read()
    result = get_list(html,url)
    print(fmt_json.dump(result))
    '''
    url = "http://esf.cq.fang.com/chushou/3_171310154.htm"
    fname = "data/list.html"
    #fname = "data/detail.html"
    html = open(fname).read()
    nurl,result = get_list(html,url)
    print(nurl)
    #result = get_detail(html,url)
    #print(result)
    #print(fmt_json.dump(lst))

if "__main__" == __name__:
    util.manage(cb)
