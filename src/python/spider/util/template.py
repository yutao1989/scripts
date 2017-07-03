#! /usr/bin/python -O
#-*- coding=utf-8 -*-

from lxml import etree
import math
import re

def get_jpath(obj, lst):
    tmp = obj
    if lst[0] == "func":
        return lst[1](obj)
    for item in lst:
        tp = type(item)
        tp_tmp = type(tmp)
        if tp in str_type:
            if tp_tmp == type({}) and item in tmp:
                tmp = tmp[item]
            else:
                return None
        elif tp == type(1):
            if tp_tmp in lst_type and item >= 0 and item < len(tmp):
                tmp = tmp[item]
            else:
                return None
        else:
            return None
    return tmp

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

def merge(mp1,mp2):
    copy_mp = mp2.copy()
    for key in mp1.keys():
        if key not in copy_mp:
            copy_mp[key] = mp1[key]
    return copy_mp

def fill_detail(key,source,target):
    if "__keys" in target and key in target["__keys"]:
        for field_info in target["__keys"][key]:
            skey = field_info[1]
            tkey = field_info[0]
            if skey in source:
                if type(source[skey]) == type({}) and "future" in source[skey]:
                    raise Exception("recursively get value is not supported yet,will consider about that.")
                else:
                    if "value" in target[tkey]:
                        target[tkey]["value"].append(source[skey])
                    else:
                        target[tkey]["value"] = [source[skey]]

def fill_data(ctx):
    if len(ctx) > 1:
        last = ctx[-1]
        for item in ctx[:-1]:
            fill_detail(last[1],last[2],item[2])
            fill_detail(item[1],item[2],last[2])

def get_context(lst):
    paths = []
    for item in lst:
        mp = {}
        for key in item[2].keys():
            if type(item[2][key]) == type({}) and "future" in item[2][key]:
                keys = item[2][key]["key"]
                if keys[0] not in mp:
                    mp[keys[0]] = [(key, keys[1])]
                else:
                    mp[keys[0]].append((key, keys[1]))
        if len(mp) > 0:
            item[2]["__keys"] = mp
        paths.append((get_path(item[1]),item[0],item[2]))
    paths.sort(lambda a1,a2:1 if a1[0]>a2[0] else (0 if a1[0]==a2[0] else -1))
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
        for key in item[2].keys():
            if type(item[2][key]) == type({}) and "future" in item[2][key]:
                if "value" in item[2][key]:
                    item[2][key] = item[2][key]["value"]
                else:
                    del item[2][key]
            if type(item[2][key]) == type([]) and len(item[2][key]) == 1:
                item[2][key] = item[2][key][0]

def get_data(key,conf,node,ctx,result):
    if conf[0] == "xpath":
        snodes = node.xpath(conf[1])
        if len(snodes) > 0:
            result[key] = [o.strip() for o in snodes]
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
        result[key] = zip(*tuple(lst))
    elif conf[0] == "func":
        result[key] = conf[1](ctx)
    elif conf[0] == "const":
        result[key] = conf[1]
    elif conf[0] == "future":
        result[key] = {"future":True,"key":(conf[1],conf[2])}
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
            config[item[0]][2](item[0],item[2],data,url)
        else:
            default_add_to_data(item[0],item[2],data,url)
    return data,url

def path_detect(path_patern):
    return lambda p,cfg,h:re.match(path_patern,p) is not None

def node_filter(score,patern=None):
    return lambda p,cfg,h:node_detect(p,cfg,h,score,patern)

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
