#!/usr/bin/env python
#encoding:UTF-8

import requests
import json
import xlwt
import datetime
import math
import os
import sys

url = ''
cookie = ''

url = sys.argv[1]
url = url.replace('\\','')
cookie = sys.argv[2]

currentPage = 1
totalPage = 1
result = []
cookie_array = cookie.replace(' ','').split(';')
cookies = {}
for i in cookie_array:
	index = i.index('=')
	if index>-1:
		cookies[i[:index]] = i[index+1:]

while currentPage<=totalPage:
	print(f'正在请求第 {currentPage} 页 ')
	req_url = ''
	if 'currentPage=1' in url:
		req_url = url.replace('currentPage=1',f'currentPage={currentPage}')
	else:
		req_url = url.replace('currentPage=2',f'currentPage={currentPage}')
	r = requests.get(req_url,cookies=cookies)
	r = json.loads(r.text)
	result = result + r['JSONObject']
	totalPage = math.ceil(r['totalItem']/20)
	currentPage = currentPage + 1

print(f'共{len(result)}条数据')

myxls=xlwt.Workbook()
sheet1=myxls.add_sheet(u'sheet',cell_overwrite_ok=True)

style = xlwt.XFStyle()  # 创建一个样式对象，初始化样式

al = xlwt.Alignment()
al.horz = 0x02      # 设置水平居中
al.vert = 0x01      # 设置垂直居中
style.alignment = al

font = xlwt.Font() # 为样式创建字体
font.name = '微软雅黑' 
font.bold = True # 黑体
# font.underline = True # 下划线
# font.italic = True # 斜体字
style.font = font # 设定样式

# 边框
borders = xlwt.Borders()
borders.left = xlwt.Borders.THIN
borders.right = xlwt.Borders.THIN
borders.top = xlwt.Borders.THIN
borders.bottom = xlwt.Borders.THIN
style.borders = borders

sheet1.col(0).width=350*20
sheet1.col(1).width=200*20
sheet1.col(2).width=220*20
sheet1.col(3).width=220*20
sheet1.col(4).width=200*20
sheet1.col(5).width=200*20
sheet1.col(6).width=200*20
sheet1.col(7).width=300*20

for x in range(0,1000):
	sheet1.row(x).height_mismatch = True
	sheet1.row(x).height=20*20



sheet1.write(0,0,'客户信息',style)
sheet1.write(0,1,'会员级别',style)
sheet1.write(0,2,'交易总额(元)',style)
sheet1.write(0,3,'交易笔数(笔)',style)
sheet1.write(0,4,'平均交易金额(元)',style)
sheet1.write(0,5,'上次交易时间',style)
sheet1.write(0,6,'当前可用积分',style)
sheet1.write(0,7,'备注(分组)',style)



font = xlwt.Font() # 为样式创建字体
font.name = '微软雅黑' 
font.bold = False
style.font = font

for i in range(0,len(result)):
	item = result[i]
	# customerName // 客户信息
	# customerLevel //会员级别
	# tradeTotal //交易总额(元)
	# tradeNum //交易笔数(笔)
	# avTrade //平均交易金额(元)
	# tradeTime //上次交易时间
	# validPoint //当前可用积分

	# 参数对应 行, 列, 值
	sheet1.write(i+1,0,item['customerName'],style)
	sheet1.write(i+1,1,str(item['customerLevel']),style)
	sheet1.write(i+1,2,str(item['tradeTotal']),style)
	sheet1.write(i+1,3,item['tradeNum'],style)
	sheet1.write(i+1,4,item['avTrade'],style)
	sheet1.write(i+1,5,item['tradeTime'],style)
	sheet1.write(i+1,6,item['validPoint'],style)
	labels = item['labels']
	for x in range(len(labels)):
		sheet1.write(i+1,7+x,labels[x]['name'],style)


name = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d-%H%M%S')
myxls.save(f'{os.path.expanduser("~")}/Desktop/{name}.xls')


