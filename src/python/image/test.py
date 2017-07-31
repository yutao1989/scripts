#! /usr/bin/python3
#-*- coding=utf-8 -*-

#import Canny
from scipy import misc
import sys
from skimage import io
import numpy as np
import math
import bisect
import random

nbs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
colors = [[255, 255, 0], [255, 204, 0], [255, 153, 0], [255, 102, 0], [255, 51, 0], [204, 255, 0], [204, 204, 0], [204, 153, 0], [204, 102, 0], [204, 51, 0], [102, 255, 0], [102, 0, 0], [51, 0, 102], [154, 50, 205], [127, 255, 0], [122, 103, 238], [34, 139, 34], [0, 100, 0]]

conf = [1.3,1.2,1.3,1.3]

rs = []

def display(img):
    io.imshow(img)
    io.show()

def modify(p2g,shape,color_result, bl=set(range(400))):
    gc = {}
    #bl = set(range(300))
    #bl = set([12])
    #p2g = p2g2
    for i in range(shape[0]):
        for j in range(shape[1]):
            if (i,j) in p2g:
                #color_result[i][j] = np.array(colors[p2g[(i,j)]%len(colors)]) 
                grp = p2g[(i,j)]
                if grp not in bl:
                    continue
                if grp not in gc:
                    gc[grp] = random.randint(0,len(colors)-1)
                color_result[i][j] = np.array(colors[gc[grp]])
            for item in rs:
                d = distance((i,j),item[0])
                if d > .97*item[1] and d < 1.03*item[1]:
                    color_result[i][j] = np.array([255,255,255])

def split_image(grey_img):
    shape = grey_img.shape
    color_result = np.ndarray(shape+(3,),"uint8")
    p2g = {}
    grp = 0
    for i in range(shape[0]):
        for j in range(shape[1]):
            if (i,j) in p2g:
                continue
            if grey_img[i][j] == 255:
                visit(grey_img,i,j,grp,p2g)
                grp += 1
    p2g2 = p2g.copy()
    g2p = merge(grey_img,p2g)
    modify(p2g,shape,color_result)
    for key in g2p.keys():
        pts = g2p[key]
        xs = [o[0] for o in pts]
        ys = [o[1] for o in pts]
        print(key,min(xs),min(ys),max(xs),max(ys))
    #modify(p2g2,shape,color_result,set([150]))
    
    return color_result

def visit(img,x,y,g,mp):
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

def merge_real(g1,g2,mp1,mp2):
    for item in mp1[g2]:
        mp1[g1].append(item)
        mp2[item] = g1

def merge(grey_img,mp):
    g2p = {}
    for key in mp.keys():
        if mp[key] not in g2p:
            g2p[mp[key]] = [key]
        else:
            g2p[mp[key]].append(key)
    dl = []
    merged = set([])
    for g in g2p.keys():
        if g in merged:
            continue
        n = find_neighbors(grey_img,g,g2p,mp)
        while n is not None:
            #if g in set([19,12]):
            if g in set(range(400)):
                print("----",g,n)
            merge_real(g,n,g2p,mp)
            merged.add(n)
            #n = find_neighbors(grey_img,g,g2p,mp)
            n = find_neighbors_by_mean(grey_img,g,g2p,mp)
    for item in merged:
        g2p.__delitem__(item)
    return g2p

def distance(p1,p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def get_mean_std(lst):
    xs = [o[0] for o in lst]
    ys = [o[1] for o in lst]
    md = math.sqrt(np.std(xs)**2 + np.std(ys)**2)
    mean = (np.mean(xs), np.mean(ys))
    mx = max([distance(o,mean) for o in lst])
    return (mean,md,mx)

def judge(d,g1,g2, mp):
    m1,d1,mx1 = get_mean_std(mp[g1])
    m2,d2,mx2 = get_mean_std(mp[g2])
    m3,d3,mx3 = get_mean_std(mp[g1]+mp[g2])
    mean_dis = distance(m1,m2)
    if mean_dis <= max(mx1,mx2)*1.1:
        return True
    elif d3< max(d1,d2)*1.2:
        return True
    else:
        md1 = distance(m1,m3)
        md2 = distance(m2,m3)
        '''
        if md1 > md2:
            if md2 < d2*.5:
                return True
        else:
            if md1 < d1*.5:
                return True
        '''
        if min(md1,md2) < min(d1,d2)*1.1 and max(mx1,mx2) > mx3*.8:
            return True
        return False

def find_neighbors_by_mean(grey_img,g,mp1,mp2):
    s = ([],{},{})
    m_p,md,mx = get_mean_std(mp1[g])
    shape = grey_img.shape
    s[0].append(0)
    s[1][0] = []
    for item in mp1[g]:
        d = distance(item,m_p)
        if d not in s[1]:
            bisect.insort(s[0],d)
            s[1][d] = [item]
        else:
            s[1][d].append(item)
        s[2][item] = item

    while len(s[0]) > 0:
        d = s[0][0]
        s[0].__delitem__(0)
        items = s[1][d]
        s[1].__delitem__(d)
        if d > mx*conf[0]:
            break
        for item in items:
            for nb in nbs:
                nx = item[0] + nb[0]
                ny = item[1] + nb[1]
                if nx >= 0 and ny >= 0 and nx < shape[0] and ny < shape[1]:
                    pass
                else:
                    continue
                if (nx,ny) not in s[2]:
                    l = distance((nx,ny),m_p)
                    if grey_img[nx][ny] == 255:
                        if judge(l,g,mp2[(nx,ny)],mp1):
                            return mp2[(nx,ny)]
                        else:
                            return None
                    if l not in s[1]:
                        bisect.insort(s[0],l)
                        s[1][l] = [(nx,ny)]
                        s[2][(nx,ny)] = s[2][item]
                    else:
                        s[1][l].append((nx,ny))
                        s[2][(nx,ny)] = s[2][item]
    return None

def find_neighbors(grey_img,g,mp1,mp2):
    s = ([],{},{})
    _,md,mx = get_mean_std(mp1[g])
    shape = grey_img.shape
    s[0].append(0)
    s[1][0] = []
    for item in mp1[g]:
        s[1][0].insert(0,item)
        s[2][item] = item

    while len(s[0]) > 0:
        d = s[0].pop()
        if d > md*conf[0]:
            break
        items = s[1][d]
        s[1].__delitem__(d)
        for item in items:
            for nb in nbs:
                nx = item[0] + nb[0]
                ny = item[1] + nb[1]
                if nx >= 0 and ny >= 0 and nx < shape[0] and ny < shape[1]:
                    pass
                else:
                    continue
                if (nx,ny) not in s[2]:
                    l = distance((nx,ny),s[2][item])
                    if grey_img[nx][ny] == 255:
                        if judge(l,g,mp2[(nx,ny)],mp1):
                            return mp2[(nx,ny)]
                        else:
                            return None
                    if l not in s[1]:
                        bisect.insort(s[0],l)
                        s[1][l] = [(nx,ny)]
                        s[2][(nx,ny)] = s[2][item]
                    else:
                        s[1][l].append((nx,ny))
                        s[2][(nx,ny)] = s[2][item]
    return None

if "__main__" == __name__:
    #path = sys.argv[1]
    #img = misc.imread(path)
    #result = Canny.performEdgeDetection(img)
    #io.imsave("data/tmp.png",result)
    img = io.imread("data/tmp.png")
    color_result = split_image(img)
    io.imsave("data/result.png",color_result)
    #display(color_result)
