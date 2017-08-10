#! /usr/bin/python3

import pymysql
import sys

host = ""
user = ""
passwd = ""
db = ""

def print_err(message):
    sys.stderr.write(message+"\n")

def batch_insert(data,cursor,sql,tpl=None):
    strs = [tpl % tuple(o) for o in data] if tpl is not None else data
    try:
        cursor.execute(sql + ",".join(strs))
    except Exception:
        tp, e,trace = sys.exc_info()
        if len(data) > 1:
            for d in data:
                batch_insert([d], cursor,sql, tpl)
        else:
            if str(e).startswith("(1062"):
                pass
            else:
                print_err("insert mysql error:")
                print_err(str(e))
                print_err(sql + strs[0])

def batch_query(cursor,sql_temp,ids):
    sql = sql_temp % ",".join(ids)
    try:
        result = cursor.execute(sql)
        if result > 0:
            data = cursor.fetchall()
            return data
        else:
            return []
    except Exception:
        tp, e,trace = sys.exc_info()
        print_err("query mysql error:")
        print_err(str(e))
        print_err(sql)
        return None

def dump_db(table, columns, data, tpl=None,needupdate=False):
    conn = pymysql.connect(host,user,passwd,db,charset="utf8")
    cursor=conn.cursor()
    start = 0
    size = 10 if not needupdate else 1
    datasize = len(data)
    sql = "insert into `%s`(`%s`) values" % (table, "`, `".join(columns))
    while start < datasize:
        sub = data[start:min(start+size,datasize)]
        batch_insert(sub, cursor,sql,tpl)
        start = start + size
    conn.commit()
    cursor.close()
    conn.close()

if "__main__" == __name__:
    print(123)
