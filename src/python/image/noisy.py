#! /usr/bin/python3
#-*- coding=utf-8 -*-

import Canny
from skimage import io,transform
import sys
import numpy as np
import math
import random
import bisect

nbs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
colors = [[255, 255, 0], [255, 204, 0], [255, 153, 0], [255, 102, 0], [255, 51, 0], [204, 255, 0], [204, 204, 0], [204, 153, 0], [204, 102, 0], [204, 51, 0], [102, 255, 0], [102, 0, 0], [51, 0, 102], [154, 50, 205], [127, 255, 0], [122, 103, 238], [34, 139, 34], [0, 100, 0]]

conf = [1.3,1.2,1.3,1.3]

def modify(p2g,shape,color_result, bl=set(range(400))):
    gc = {}
    for i in range(shape[0]):
        for j in range(shape[1]):
            if (i,j) in p2g:
                grp = p2g[(i,j)]
                if grp in bl:
                    continue
                if grp not in gc:
                    gc[grp] = random.randint(0,len(colors)-1)
                color_result[i][j] = np.array(colors[gc[grp]])
            else:
                color_result[i][j] = np.array([0,0,0])

def visit(img,x,y,g,mp,flt):
    count = 1
    mp[(x,y)] = g
    shape = img.shape
    q = [(x,y)]
    while len(q) > 0:
        item = q.pop()
        for nb in nbs:
            nx = item[0]+nb[0]
            ny = item[1]+nb[1]
            if (nx,ny) in mp:
                continue
            if nx >= 0 and ny >= 0 and nx < shape[0] and ny < shape[1]:
                if img[nx][ny] == 255:
                    mp[(nx,ny)] = g
                    q.insert(0,(nx,ny))
                    count += 1
    if count < 3:
        flt.add(g)

def calc_neighbors(grey_img):
    shape = grey_img.shape
    result = np.ndarray(shape+(4,))
    for i in range(shape[0]):
        for j in range(shape[1]):
            if grey_img[i][j] != 255:
                result[i][j] = np.array([-1,-1,-1,-1])
                continue
            idx = 1
            flg = [o==5 for o in range(4)]
            r = [shape[0],shape[0],shape[1],shape[1]]
            while not all(flg):
                if not flg[1] and i+idx < shape[0]:
                    if grey_img[i+idx][j] == 255:
                        r[1] = idx
                        flg[1] = True
                if not flg[0] and i-idx >= 0:
                    if grey_img[i-idx][j] == 255:
                        r[0] = idx
                        flg[0] = True
                if not flg[3] and j+idx < shape[1]:
                    if grey_img[i][j+idx] == 255:
                        r[3] = idx
                        flg[3] = True
                if not flg[2] and j-idx >= 0:
                    if grey_img[i][j-idx] == 255:
                        r[2]= idx
                        flg[2] = True
                idx += 1
                if i+idx >= shape[0] and i-idx < 0 and j+idx >= shape[1] and j-idx < 0:
                    break
            result[i][j] = np.array(r)
    return result

def split_image(grey_img):
    shape = grey_img.shape
    color_result = np.ndarray(shape+(3,),"uint8")
    p2g = {}
    grp = 0
    bls = set()
    for i in range(shape[0]):
        for j in range(shape[1]):
            if (i,j) in p2g:
                continue
            if grey_img[i][j] == 255:
                visit(grey_img,i,j,grp,p2g,bls)
                grp += 1
    modify(p2g,shape,color_result,bls)
    return color_result

def remove_point(dist,img):
    nimg = img.copy()
    shape = img.shape
    for i in range(shape[0]):
        for j in range(shape[1]):
            if img[i][j] == 255:
                d = dist[i][j]
                if d[0] > 10 and d[1] > 10:
                    nimg[i][j] = 0
                elif d[2] > 10 and d[3] > 10:
                    nimg[i][j] = 0
    return nimg

def cut_and_link(img):
    dist = calc_neighbors(img)
    shape = img.shape
    for j in range(shape[1]):
        for i in range(shape[0]):
            pass

def split_range(img,region,isx,m="density",cp=1):
    rx = range(region[0][0],region[1][0])
    ry = range(region[0][1],region[1][1])
    params = None
    if isx:
        params = [rx,ry]
    else:
        params = [ry,rx]
    items = []
    tmp = []
    dd = -1
    for i in params[0]:
        n = None
        if m == "std":
            n = np.std([j for j in params[1] if img[i][j]==255]) if isx else np.std([j for j in params[1] if img[j][i]==255])
        else:
            n = sum([1 if img[i][j]==255 else 0 for j in params[1]]) if isx else sum([1 if img[j][i]==255 else 0 for j in params[1]])
        if len(tmp) < 2:
            tmp.insert(0,n)
        else:
            if cp == 1:
                l = tmp[0]
                if n>l:
                    if (n-l)/max(l,1) >= 1.5:
                        items.append((i-1,-1))
                else:
                    if (l-n)/max(n,1) >= 1.5:
                        items.append((i,1))
            elif cp == 2:
                md = tmp[0]
                l = tmp[-1]
                if md <= l and md >= n:
                    items.append((i-1,dd))
                    dd = -dd
            tmp.pop()
            tmp.insert(0,n)
    pairs = []
    for i in range(len(items)):
        item = items[i]
        if i+1 < len(items):
            if item[1] == -1 and items[i+1][1] == 1:
                pairs.append((item[0],items[i+1][0]))
    return pairs

def distance(p1,p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def is_symmetry_and_middle(img,region):
    rx = range(region[0][0],region[1][0])
    ry = range(region[0][1],region[1][1])
    shape = (region[1][0]-region[0][0],region[1][1]-region[0][1])
    md_p = (np.mean([region[0][0],region[1][0]]), np.mean([region[0][1],region[1][1]]))
    pts = [(i,j) for i in rx for j in ry if img[i][j]==255]
    m_p = (np.mean([o[0] for o in pts]),np.mean([o[1] for o in pts]))
    std = np.mean([distance(o,m_p) for o in pts])
    md_m_d = distance(m_p,md_p)
    size = distance(shape,(0,0))
    if md_m_d/size < .1 and std/size > .25:
        return True
    else:
        return False

def find_by_start(img,region,ht):
    shape = img.shape
    '''
    r = region
    n = 0
    score = 0
    while r[1][1] < shape[1]:
        s1 =
        s2 =
        score += (s1+s2) 
        r = [(r[0][0],r[1][1]),(r[1][0],r[1][1]+ht)]
    '''

def find_size(img,region,ht):
    shape = img.shape
    lu = region[0]
    while lu[1] + ht < shape[1]:
        r2 = [lu,(region[1][0],lu[1]+ht)]
        if is_symmetry_and_middle(img,r2):
            print("1 "+" ".join([str(o2) for o1 in r2 for o2 in o1]))
            pass
        lu = (region[0][0],lu[1]+1)

def cut_by_line_density(img):
    shape = img.shape
    size = distance(shape,(0,0))
    pairs = []
    nmg = img.copy()
    pairs = split_range(img,[(0,0),shape],True)
    for item in pairs:
        ht = item[1]-item[0]
        if ht/size < .08: 
            continue
        #find_size(img,[(item[0],0),(item[1],shape[1])],ht)
        for j in range(shape[1]):
            nmg[item[0]][j] = 255
            nmg[item[1]][j] = 255
    return nmg

def get_region_value(img,region):
    rx = range(region[0][0],region[1][0])
    ry = range(region[0][1],region[1][1])
    area = (region[0][0]-region[1][0])*(region[0][1]-region[1][1])
    pts = [(o1,o2) for o1 in rx for o2 in ry if img[o1][o2]==255]
    d = len(pts)/area
    horizontal = (region[1][1]-region[0][1])/img.shape[1]
    result = int((d + horizontal)*1000)
    return result

def get_overlap(o1,o2):
    if o1[0] >= o2[1] or o2[0] >= o1[1]:
        return 0
    else:
        return min(o1[1],o2[1])-max(o1[0],o2[0])

def get_maximum(img,p,mp,a,b):
    idx = 1
    u = p[1]
    d = p[1]
    while (p[0],p[1]+idx) not in mp or (p[0],p[1]-idx) not in mp:
        if (p[0],p[1]+idx) not in mp:
            u = p[1]+idx
        if (p[0],p[1]-idx) not in mp:
            d = p[1]-idx
        idx += 1
        if p[1]+idx>=img.shape[1] and p[1]-idx<0:
            break
    u = u+1
    thr = .94
    for l1 in range(0,p[0]):
        for l2 in range(p[0]+1,img.shape[0]):
            print(l1,l2)
            region = [(l1,d),(l2,u)]
            size = (region[0][0]-region[1][0])*(region[0][1]-region[1][1])
            pts = [2 if (o1,o2) in mp else 1 for o1 in range(region[0][0],region[1][0]) for o2 in range(region[0][1],region[1][1]) if (o1,o2) in mp or img[o1][o2]==255]
            bls = sum(pts)-len(pts)
            ws = len(pts)-bls
            if bls/size < .05:
                if ws in b:
                    if len(b[ws]) < 10:
                        b[ws].append(region)
                else:
                    b[ws] = [region]
                    bisect.insort(a,ws)
                    if len(a) > 100:
                        del a[0]

def find_widest_rectangle(img):
    shape = img.shape
    mp = {}
    nmg = img.copy()
    for i in range(shape[0]):
        lines = []
        j = 0
        l = -1
        while j < shape[1]:
            if img[i][j] == 0:
                if l == -1:
                    l = j
            elif img[i][j] == 255:
                if l != -1:
                    lines.append((l,j))
                    l = -1
            j += 1
        if l != -1:
            lines.append((l,shape[1]))
        threshold = .99
        lines2 = []
        for i1 in range(len(lines)):
            for i2 in range(i1+1,len(lines)):
                ll = (lines[i2][1]-lines[i1][0])
                pts = sum([o[1]-o[0] for o in lines[i1:i2+1]])
                if pts/ll >= threshold:
                    lines2.append((lines[i1][0],lines[i2][1]))
            lines2.append(lines[i1])
        lines2.sort(key=lambda x:x[1]-x[0])
        mp[i] = lines2[-1]
        #for jj in range(*lines2[-1]):
        #    nmg[i][jj] = 255
    for i in range(1,shape[0]-1):
        l = mp[i-1] if i-1 in mp else (0,0)
        t = mp[i] if i in mp else (0,0)
        n = mp[i+1] if i+1 in mp else (0,0)
        lt = get_overlap(l,t)
        nt = get_overlap(n,t)
        isP = False
        lo = lt/max(l[1]-l[0],t[1]-t[0],1)
        no = nt/max(n[1]-n[0],t[1]-t[0],1)
        ppp = (.9,.2)
        if t[1]-t[0] > .5*shape[1]:
            isP = True
        elif lo >= ppp[0] or no >= ppp[0]:
            isP = True
        if not isP:
            #for jj in range(*mp[i]):
            #    nmg[i][jj] = 255
            del mp[i]
    i = 0
    while i < shape[0]-3:
        t1 = mp[i] if i in mp else (0,0)
        t2 = mp[i+1] if i+1 in mp else (0,0)
        t3 = mp[i+2] if i+2 in mp else (0,0)
        t4 = mp[i+3] if i+3 in mp else (0,0)
        o12 = get_overlap(t1,t2)/max(t1[1]-t1[0],t2[1]-t2[0],1)
        o23 = get_overlap(t3,t2)/max(t3[1]-t3[0],t2[1]-t2[0],1)
        o34 = get_overlap(t3,t4)/max(t3[1]-t3[0],t4[1]-t4[0],1)
        if o12 == 0 and o23 >= .95 and o34 == 0:
            del mp[i+1]
            del mp[i+2]
            i = i + 3
        else:
            i += 1
    mp2 = {}
    for i in range(0,shape[0]) :
        if i in mp:
            for jj in range(*mp[i]):
                mp2[(i,jj)] = 1
    aa = []
    bb = {}
    for i in range(shape[0]):
        for j in range(shape[1]):
            if (i,j) not in mp2:
                print((i,j))
                get_maximum(img,(i,j),mp2,aa,bb)
    print(aa)
        
    return nmg


def resize(img):
    shape = img.shape
    big = np.ndarray((shape[0]*2,shape[1]*2,3),"uint8")
    for i in range(shape[0]):
        for j in range(shape[1]):
            big[i*2][2*j] = img[i][j].copy()
            big[i*2][2*j+1] = img[i][j].copy()
        big[i*2+1] = big[i*2].copy()
    return big

if "__main__" == __name__:
    '''
    path = sys.argv[1]
    img = io.imread(path)
    img = resize(img)
    result = Canny.performEdgeDetection(img)
    io.imsave("data/tmp.png",result)
    '''
    img = io.imread("data/tmp.png")
    dist =  calc_neighbors(img)
    img = remove_point(dist,img)
    #img = cut_by_line_density(img)
    img = find_widest_rectangle(img)
    io.imsave("data/result.jpg",img)
    sys.exit(0)
    color_result = split_image(img)
    io.imsave("data/result.jpg",color_result)
    #display(color_result)
