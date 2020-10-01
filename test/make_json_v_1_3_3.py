"""
Script used to create 'test_file_v_1_3_3.json' as a reference file 
that must be readable by subsequent versions of GTC.  

The unit test 'test_json_v_1_3_3.py' expects to find 
'test_file_v_1_3_3.json' in the local directory.

"""
import os
from GTC import *

ar = persistence.Archive()

x = ureal(1,1)
y = ureal(2,1)
z = result( x + y )

ar.add(x=x,y=y,z=z)

x1 = ureal(1,1,3,label='x')
y1 = ureal(2,1,4,label='y')
z1 = result( x1 + y1 )

ar.add(z1=z1)

x2 = ureal(1,1,independent=False)
y2 = ureal(2,1,independent=False)

r = 0.5
set_correlation(r,x2,y2)

z2 = result( x2 + y2 )

ar.add(x2=x2,y2=y2,z2=z2)
    
x3,y3 = multiple_ureal([1,2],[1,1],4)

r = 0.5
set_correlation(r,x3,y3)

z3 = result( x3 + y3 )

ar.add(x3=x3,y3=y3,z3=z3)

x4 = ucomplex(1,[10,2,2,10],5)
y4 = ucomplex(1-6j,[10,2,2,10],7)

z4 = result( log( x4 * y4 ) )

ar.add(x4=x4,y4=y4,z4=z4)

fname = 'ref_file_v_1_3_3.json'
wdir =  os.path.dirname(__file__)
path = os.path.join(wdir,fname)

with open(path,'w') as f:
    persistence.dump_json(f,ar,indent=2)

f.close()
