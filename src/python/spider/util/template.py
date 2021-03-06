#! /usr/bin/python -O
#-*- coding=utf-8 -*-

import sys
from lxml import etree
import math
import re
import util
import traceback

def get_jpath(obj, lst, default=None,p=None):
    tmp = obj
    if lst[0] == "__func":
        return lst[1](obj)
    elif lst[0] == "__const":
        return lst[1]
    for item in lst:
        if isinstance(item,str):
            if isinstance(tmp,dict) and item in tmp:
                tmp = tmp[item]
            else:
                return default
        elif isinstance(item,int):
            if isinstance(tmp,list) and item >= 0 and item < len(tmp):
                tmp = tmp[item]
            else:
                return default
        else:
            return default
    return tmp if p is None else p(tmp)

def get_path(node):
    p = node.getparent()
    c = node
    paths = []
    while p is not None:
        n = int(math.ceil(math.log(len(p.getchildren()),10)))
        temp = "%%.%dd" % max(n,1)
        paths.append(temp % p.index(c))
        c = p
        p = p.getparent()
    return "_".join(paths[::-1])

def is_too_complicate(src,obj):
    if src is obj:
        return True
    if isinstance(obj,list) or isinstance(obj,tuple):
        result = False
        for o in obj:
            if is_too_complicate(src,o):
                result = True
                break
        return result
    elif isinstance(obj,dict):
        for k in obj.keys():
            if is_too_complicate(src,obj[k]):
                result = True
                break
        return result
    else:
        return False

def fill_detail(key,source,target):
    if "__keys" in target and key in target["__keys"]:
        for field_info in target["__keys"][key]:
            skey = field_info[1]
            tkey = field_info[0]
            if skey in source:
                if isinstance(source[skey],dict) and "future" in source[skey]:
                    if is_too_complicate(target[tkey]["value"],source[skey]["value"]):
                        raise Exception("recursively get value of self is not allowed")
                    target[tkey]["value"].append(source[skey]["value"])
                else:
                    target[tkey]["value"].append(source[skey])

def fill_data(ctx):
    if len(ctx) > 1:
        last = ctx[-1]
        for item in ctx[:-1]:
            fill_detail(last[1],last[2],item[2])
            fill_detail(item[1],item[2],last[2])

def get_single(value):
    if isinstance(value,list):
        if len(value) == 1:
            count = 10
            while isinstance(value,list) and len(value)==1 and count >= 0:
                value = value[0]
                count -= 1
            if count > 0:
                return value
            else:
                return None
        elif len(value)>1:
            nv = []
            for o in value:
                r = get_single(o)
                if r is not None:
                    nv.append(r)
            return nv
        else:
            return None
    else:
        return value

def get_context(lst):
    paths = []
    for item in lst:
        mp = {}
        for key in item[2].keys():
            if isinstance(item[2][key],dict) and "future" in item[2][key]:
                keys = item[2][key]["key"]
                if keys[0] not in mp:
                    mp[keys[0]] = [(key, keys[1])]
                else:
                    mp[keys[0]].append((key, keys[1]))
        if len(mp) > 0:
            item[2]["__keys"] = mp
        paths.append((get_path(item[1]),item[0],item[2]))
    kf = lambda o:o[0]
    paths.sort(key=kf)
    ctx = []
    for item in paths:
        if len(ctx) == 0 or item[0].startswith(ctx[-1][0]+"_"):
            ctx.append(item)
        else:
            while len(ctx) > 0 and not item[0].startswith(ctx[-1][0]+"_"):
                fill_data(ctx)
                ctx.pop()
            ctx.append(item)
    while len(ctx) > 0:
        fill_data(ctx)
        ctx.pop()
    for item in lst:
        if "__keys" in item[2]:
            del item[2]["__keys"]
        rks = []
        for key in item[2].keys():
            value = None
            if isinstance(item[2][key],dict) and "future" in item[2][key]:
                value = item[2][key]["value"]
            else:
                value = item[2][key]
            value = get_single(value)
            if value is None or (hasattr(value,"__len__") and value.__len__()==0) or (isinstance(value,str) and value.strip()==""):
                rks.append(key)
            elif item[2][key] is not value:
                item[2][key] = value
        for key in rks:
            item[2].__delitem__(key)

def protect_call(f,params):
    try:
        return f(*params)
    except:
        tp,e,tb = sys.exc_info()
        util.log_msg("call user defined function error:<%s>,traceback:%s" % (str(e),str(traceback.format_tb(tb))),"error")
        return None

def get_data(key,conf,node,ctx,result):
    if conf[0] == "xpath":
        snodes = node.xpath(conf[1])
        if len(snodes) > 0:
            result[key] = [o.strip() for o in snodes]
    elif conf[0] == "xpath_lambda":
        result[key] = [o1 for o in node.xpath(conf[1]) for o1 in [protect_call(conf[2],(o,get_jpath(ctx,["entrance"])))] if o1 is not None and (not hasattr(o1,"__len__") or o1.__len__()>0)]
    elif conf[0] == "mxpath":
        lst = []
        length = -1
        default = []
        for x in conf[1]:
            snodes = node.xpath(x)
            item = [o.strip() for o in snodes] if len(snodes) > 0 else default
            if length == -1 and len(item) > 0:
                length = len(item)
                for i in range(length):
                    default.append("")
            else:
                if length != len(item):
                    # do something
                    print("size not equal")
            lst.append(item)
        result[key] = list(zip(*tuple(lst)))
    elif conf[0] == "func":
        result[key] = protect_call(conf[1],(ctx,))
    elif conf[0] == "const":
        result[key] = conf[1]
    elif conf[0] == "future":
        result[key] = {"future":True,"key":(conf[1],conf[2]),"value":[]}
    elif conf[0] == "jpath":
        result[key] = get_jpath(ctx, conf[1])

def template(key, data, field_confs, result):
    for node in data["nodes"]:
        mp = {}
        for conf in field_confs:
            get_data(conf[0],conf[1],node,data,mp)
        if len(mp) > 0:
            result.append((key,node,mp))

def default_add_to_data(key, item, data, url):
    data.append((key,item))

def parse(html,config, entrance):
    result = []
    tree = etree.HTML(html)
    for key in config.keys():
        conf = config[key]
        # used for html or xml file format only
        nodes = tree.xpath(conf[0])
        if len(nodes) > 0:
            template(key, {"nodes":nodes,"entrance":entrance},conf[1],result)
    get_context(result)
    data = []
    url = []
    for item in result:
        if len(config[item[0]]) > 2:
            d,u = config[item[0]][2](item[0],item[2])
            for o in d:
                data.append((item[0],o))
            for o in u:
                url.append(o)
        else:
            data.append((item[0],item[2]))
    return data,url

def path_detect(path_patern):
    return lambda p,cfg,h,entry:re.match(path_patern,p) is not None

def node_filter(score,patern=None):
    return lambda p,cfg,h,entry:node_detect(p,cfg,h,score,patern)

def node_detect(p,cfg,h,score=.5,patern=None):
    if patern is not None:
        if re.match(patern,p) is None:
            return False
    tree = etree.HTML(h)
    length = len(cfg)
    m = 0
    for key in cfg.keys():
        if len(tree.xpath(cfg[key][0])) > 0:
            m = m + 1
    if m*1./length >= score:
        return True
    else:
        return False
