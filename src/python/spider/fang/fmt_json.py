#! /usr/bin/python3

import re

basic_tps = set([type(""),type(1),type(.1)])
indent = 4

def fmt(indent,key,value,lst):
    if key is None:
        lst.append("%s%s" % (indent, value))
    else:
        lst.append("%s\"%s\": %s" % (indent,key,value))

def format_json(name,obj,n,has_bro,adder):
    indent_str = indent*n*" "
    if isinstance(obj,list) or isinstance(obj,tuple):
        paras = (indent_str,None,"[") if name is None else (indent_str,name,"[")
        adder(*paras)
        for item in obj[:-1]:
            format_json(None,item,n+1,True,adder)
        item = obj[-1]
        format_json(None,item,n+1,False,adder)
        adder(indent_str,None,"]" if not has_bro else "],")
    elif isinstance(obj,dict):
        paras = (indent_str,None,"{") if name is None else (indent_str,name,"{")
        adder(*paras)
        keys = list(obj.keys())
        keys.sort()
        for k in keys[:-1]:
            format_json(k,obj[k],n+1,True,adder)
        k = keys[-1]
        format_json(k,obj[k],n+1,False,adder)
        adder(indent_str,None,"}" if not has_bro else "},")
    else:
        value = None
        if isinstance(obj,str):
            value = "\"%s\"" % obj
            value = re.sub("[\r\n]+","\t",value)
        elif isinstance(obj,float):
            value = "%.10f" % obj
        elif isinstance(obj,int):
            value = str(obj)
        else:
            raise Exception("unknown type:",type(obj))
        adder(indent_str,name,value+"," if has_bro else value)

def dump(obj):
    lst = []
    adder = lambda x,y,z:fmt(x,y,z,lst)
    format_json(None,obj,0,False,adder)
    return "\n".join(lst)
