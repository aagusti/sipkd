x1 = '2015-00001'
x2 = '2015-00002'
x3 = x2.split('/')
xs = ''
import re
for x in x3:
    if xs:
        xs +='/'
    xs += x[2:]
print re.sub('-','',xs)

