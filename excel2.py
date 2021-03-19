#!/usr/bin/envpython
#encoding:UTF-8

import requests
import json
import xlwt
import datetime
import math
import os
import sys

#加载本地json文件，返回为对象
def load_json(path):
	if not os.path.exists(path):
		print(f'loadjson失败：{path}不存在')
	with open(path) as f:
		return json.load(f)

result=load_json('./表格.json')

myxls=xlwt.Workbook()
sheet1=myxls.add_sheet(u'sheet',cell_overwrite_ok=True)

style=xlwt.XFStyle()#创建一个样式对象，初始化样式

al=xlwt.Alignment()
al.horz=0x02#设置水平居中
al.vert=0x01#设置垂直居中
style.alignment=al

font=xlwt.Font()#为样式创建字体
font.name='微软雅黑'
font.bold=True#黑体
#font.underline=True#下划线
#font.italic=True#斜体字
style.font=font#设定样式

#边框
borders=xlwt.Borders()
borders.left=xlwt.Borders.THIN
borders.right=xlwt.Borders.THIN
borders.top=xlwt.Borders.THIN
borders.bottom=xlwt.Borders.THIN
style.borders=borders

sheet1.col(0).width=350*20
sheet1.col(1).width=200*20
sheet1.col(2).width=220*20
sheet1.col(3).width=220*20
sheet1.col(4).width=200*20
sheet1.col(5).width=200*20
sheet1.col(6).width=200*20
sheet1.col(7).width=300*20
sheet1.col(8).width=300*20

for x in range(0,1000):
	sheet1.row(x).height_mismatch=True
	sheet1.row(x).height=20*20

columns=result['data']['value']['columns']

sheet1.write(0,0,'统计日期',style)
sheet1.write(0,1,'来源名称',style)
sheet1.write(0,2,'商品名称',style)

result
for x in range(len(columns)):
	sheet1.write(0,3+x,columns[x]['cells'][0]['value'],style)


font=xlwt.Font()#为样式创建字体
font.name='微软雅黑'
font.bold=False
style.font=font


before_rows=result['data']['value']['rows']
after_rows=result['data']['value']['values']

total_rows=len(before_rows)

for i in range(0,total_rows):
	row1=before_rows[i]
	row2=after_rows[i]
	#customerName//客户信息
	#customerLevel//会员级别
	#tradeTotal//交易总额(元)
	#tradeNum//交易笔数(笔)
	#avTrade//平均交易金额(元)
	#tradeTime//上次交易时间
	#validPoint//当前可用积分

	row1_cell_count=len(row1['cells'])
	for j in range(row1_cell_count):
		row1_cell=row1['cells'][j]
		#参数对应行,列,值
		sheet1.write(i+1,j,str(row1_cell['value']),style)

	row2_cell_count=len(row2)
	for j in range(row2_cell_count):
		row2_cell=row2[j]
		#参数对应行,列,
		sheet1.write(i+1,row1_cell_count+j,str(row2_cell['v']),style)


name=datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d-%H%M%S')
myxls.save(f'{os.path.expanduser("~")}/Desktop/{name}.xls')


