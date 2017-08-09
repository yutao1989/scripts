#! /usr/bin/python3

blanks = set([" ","\t","\n"])
textc = set(["'","\""])
nc = set([str(o) for o in list(range(10))+["."]])
obj_s = set(["[","{"])
obj_e = set(["]","}"])
alpha_cs = set([chr(o) for o in range(ord("a"),ord("a")+26)]+[chr(o) for o in range(ord("A"),ord("A")+26)]+[chr(o) for o in range(ord("0"),ord("0")+10)]+["_","."])
bool_set = set(["true","false"])

is_strict = False

def update_mp(mp,value,fv=False):
    if fv:
        assert "___" in mp
        mp[mp["___"]] = value
        del mp["___"]
    else:
        assert "___" not in mp
        mp["___"] = value

def parse_string(v,idx,force=False):
    if v[idx] in textc:
        sc = v[idx]
        idx+=1
        sidx = idx
        while idx < len(v) and v[idx] !=sc:
            idx += 1
        if idx < len(v) and v[idx] == sc:
            return idx,v[sidx:idx],None
        else:
            raise Exception("invalid data")
    else:
        sidx = idx
        isNumber = True
        dots = 0
        while idx<len(v) and v[idx] in alpha_cs:
            if isNumber:
                if v[idx] in nc:
                    if v[idx] == ".":
                        dots += 1
                    assert dots <= 1
                else:
                    assert dots == 0
                    isNumber = False
            else:
                assert v[idx] != "."
            idx += 1
        value = v[sidx:idx]
        assert idx < len(v)
        tp = None
        if isNumber:
            if dots == 0:
                value = int(value)
                tp = True
            else:
                value = float(value)
                tp = True
        else:
            tmp = value if is_strict else value.lower()
            if tmp in bool_set:
                value = bool(tmp)
                tp = True
            else:
                tp = False
        if force:
            assert not tp
        return idx-1,value,tp

def fake_assert(q,condition):
    if not condition:
        if is_strict:
            raise Exception("")
        else:
            del q[:]
            return True
    return False

def parse(v):
    q = []
    idx = 0
    result = []
    while idx < len(v):
        if (not is_strict and len(q)==0 and v[idx] not in obj_s) or v[idx] in blanks:
            idx += 1
            continue
        if v[idx] in obj_s:
            q.append((v[idx],list() if v[idx]=="[" else dict()))
        elif v[idx] in obj_e:
            if fake_assert(q, (v[idx]=="]" and q[-1][0] == "[") or (v[idx]=="}" and q[-1][0] == "{")):
                idx+= 1
                continue
            item = q.pop()
            if len(q) == 0:
                result.append(item[1])
                continue
            else:
                if q[-1][0] in set([":",","]):
                    q.pop()
                else:
                    if fake_assert(q, q[-1][0]=="[" and len(q[-1][1])==0):
                        idx+=1
                        continue
                if q[-1][0] == "[":
                    q[-1][1].append(item[1])
                elif q[-1][0] == "{":
                    update_mp(q[-1][1],item[1],True)
                else:
                    raise Exception("could not be here,something must be wrong")
        elif v[idx] in textc or v[idx] in alpha_cs:
            idx, value,tp = parse_string(v,idx,is_strict)
            if fake_assert(q, len(q)>0):
                idx+=1
                continue
            r = 0
            if q[-1][0] in set([":",","]):
                r = 1 if q[-1][0]==":" else 2
                q.pop()
            else:
                if fake_assert(q, q[-1][0] in obj_s and len(q[-1][1])==0):
                    idx+=1
                    continue
            if q[-1][0] == "[":
                q[-1][1].append(value)
            elif q[-1][0] == "{":
                update_mp(q[-1][1],value,tp if tp is not None else (True if r==1 else False))
            else:
                raise Exception("could not be here,something must be wrong")
        elif v[idx] == ":":
            if fake_assert(q, len(q)>0 and q[-1][0]=="{" and "___" in q[-1][1]):
                idx+=1
                continue
            q.append((":",None))
        elif v[idx] == ",":
            if fake_assert(q, len(q)>0 and q[-1][0] in obj_s and len(q[-1][1])>0 and (q[-1][0]=="[" or "___" not in q[-1][1])):
                idx+=1
                continue
            q.append((",",None))
        else:
            raise Exception("could not be here,something must be wrong")
        idx += 1
    assert len(q) == 0
    return result


if "__main__" == __name__:
    tmp = '{}{"page_type":"1",a:[],"user_id":5379806062,"max_behot_time":0,"count":20,"as":"A1E51958393A1EA","cp":"5989DA615EAACE1","a":1}'
    print(parse(tmp))
