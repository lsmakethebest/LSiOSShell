
#!/usr/bin/env python3
#coding:utf-8

import sys
import os

def os_popen(cmd):
    # 执行 os.system(cmd)，返回执行结果
    return os.popen(cmd).read()


path = sys.argv[1]
name = os.path.basename(path)
result = os_popen(f'otool -V -s __TEXT __const "{path}" | grep "@(#)PROG" -A 5')
print('------------查看PROJECT名字，然后在opensource查看源码--------------------------')
print('源码地址：https://opensource.apple.com/tarballs/\n')
# print(result)
result=result.split('\n')
new_result = ''
for i in result:
	# print(i.split('|'))
	if i:
		new_result = new_result + i.split('|')[1]

print(new_result)
print('')
print('------------可查看详细版本号---------------------------------------------------')
result = os_popen(f'otool -L "{path}" | grep "{name}"')
print(result)

