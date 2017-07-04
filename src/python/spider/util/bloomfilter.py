import struct
import hashlib
import os

class bloomfilter():
    def __init__(self,bfile="data/.bloomfilter"):
        self.bfile = bfile
        self.fmt = "32768H"
        self.read_data(bfile)

    def read_data(self,bfile):
        if os.path.exists(bfile):
            tmp_data = list(struct.unpack(self.fmt,open(bfile,"rb").read()))
            self.data = [tmp_data[i*4096:(i+1)*4096] for i in range(8)]
        else:
            self.data = [[0]*4096]*8

    def query_set_bit(self,idx,value):
        tmp_data = self.data[idx]
        sidx = value/16
        bidx = value%16
        v = 1<<bidx
        if (tmp_data[sidx] & v) == 0:
            tmp_data[sidx] = tmp_data[sidx] | v
            return True
        else:
            return False

    def exists(self,url):
        md5 = hashlib.md5(url).hexdigest()
        exist = True
        for i in range(8):
            if self.query_set_bit(i,int(md5[i*4:i*4+4],16)):
                exist = False
        return exist

    def close(self):
        prms = tuple([self.fmt] + [x for y in self.data for x in y])
        open(self.bfile,"wb").write(struct.pack(*prms))
