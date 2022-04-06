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

type_str = sys.argv[1]
url = sys.argv[2]
url = url.replace('\\','')
cookie = sys.argv[3]
current_page_string = ''
list_key = [];
total_count_key = [];
page_size_count = 0
items = []

# type = '1' # 活动报表(queryListData)       https://tmc.sale.tmall.com/page/campaign/sale.htm?campaignId=29019
# type = '2' # 会员信息(ecrm_member_list)    https://ecrm.taobao.com/p/customer/ecrmMemberList.htm?spm=a1za3.8127598.0.0.62bd8573285BzV&groupId=11349528028
# type = '3' # 已选(querySelectedItemList)  https://aliyx.tmall.com/shopAct/edit.html?spm=a21y7.8602192.0.0.58a11b58da00wL#/items/16522155128?_k=2m7wyh
# type = '4' #我是卖家营销工作台店铺宝编辑活动(getItemList) https://shell.mkt.taobao.com/shopAct/getItemList?activityId=17986203561&itemIdOrName=&outerId=&cateId=&auctionStatus=0&pageNo=1&pageSize=10
# type = '5' #我是卖家营销工作台店铺宝(getList)                   https://shell.mkt.taobao.com/shopAct/index#/?spm=a21y7.12701734.0.0.45c85252vHPlVT&tabKey=custom
# type = '6' #官方大促天猫520礼遇季(queryListData)                   https://sale.tmall.com/page/campaign/sale.htm?campaignId=31858
# type = '7' #活动分析>预售活动详情(getItemListLive)       https://sycm.taobao.com/datawar/activity/presell?activityId=20851303&activityStatus=3&dateRange=2021-10-21%7C2021-10-21&dateType=today&spm=a21ag.8205355.0.0.248e50a5Lcda3d

def handle_type1_price(item):
	price = ''
	if item['originalPriceMin'] == item['originalPriceMax']:
		price = item["originalPriceMin"]
	else:
		price = f'{item.get("originalPriceMin")}~{item.get("originalPriceMax")}'
	return price

def handle_type4_name(item,key):
	if key == 'itemName':
		return item['itemDesc']['desc'][0]['text']
	elif key == 'code':
		text = item['itemDesc']['desc'][1]['text']
		index = text.find('编码')
		return text[index+3:]
	elif key == 'pric':
		return item['managerPrice']['currentPrice'].replace(' ','').replace('￥','')


def handle_type4_operation(item,key):
	if key == 'selected':
		if item['selected'] == True:
			return '已经参加'
		else:
			return "未参加"
	if key == 'price':
		price = '￥' + str(item['price'])
		price.replace('.00','')
		return price
	if key == 'lowerPriceStr':
		if item.get('itemRiskDTO'):
			return item['itemRiskDTO']['lowerPriceStr']
		else:
			price = '￥' + str(item['price'])
			price.replace('.00','')
			return price
	


def handle_type6_price(item,key):
	if item['originalPriceMin'] == item['originalPriceMax']:
		return str(item['originalPriceMin']).replace('.0','')
	else:
		text = str(item['originalPriceMin']) + '-' + str(item['originalPriceMax'])
		text = text.replace('.0','')
		return text

def handle_type8_cycleCrc(item,key):
	keys = key.split(':')
	value = item[keys[0]][keys[1]]
	if value:
		value = value*100
		return "{:.2f}".format(value)+'%'
	else:
		return ''


if type_str == '1':
	current_page_string = 'currentPage'
	list_key = ['data','list'];
	total_count_key = ['data','total']
	page_size_count = 10
	items = [
			{
				"key":"itemName",
				"name":"商品标题",
				"width":700,
				"func":handle_type4_name
			},
			{
				"key":"itemId",
				"name":"ID",
				"width":220
			},
			{
				"key":"code",
				"name":"编码",
				"width":220,
				"func":handle_type4_name
			},
			{
				"key":"price",
				"name":"价格",
				"width":220,
				"func":handle_type4_name
			},
			{
				"key":"quantity_m",
				"name":"库存",
				"width":220,
			},
			{
				"key":"soldQuantity_m",
				"name":"总销量",
				"width":220
			},
			{
				"key":"upShelfDate_m:value",
				"name":"创建时间",
				"width":220
			},
			{
				"key":"upShelfDate_m:status:text",
				"name":"状态",
				"width":300
			}
		]

if type_str == '2':
	current_page_string = 'currentPage'
	list_key = ['JSONObject'];
	total_count_key = ['totalItem']
	page_size_count = 20
	items = [
			{
				"key":"customerName",
				"name":"客户信息",
				"width":350
			},
			{
				"key":"customerLevel",
				"name":"会员级别",
				"width":220
			},
			{
				"key":"tradeTotal",
				"name":"交易总额(元)",
				"width":220
			},
			{
				"key":"tradeNum",
				"name":"交易笔数(笔)",
				"width":220
			},
			{
				"key":"avTrade",
				"name":"平均交易金额(元)",
				"width":220
			},
			{
				"key":"tradeTime",
				"name":"上次交易时间",
				"width":220
			},
			{
				"key":"validPoint",
				"name":"当前可用积分",
				"width":220
			},
			{
				"key":"labels:name",
				"name":"备注(分组)",
				"width":300
			}
		]
elif type_str == '3':
	current_page_string = 'page'
	list_key = ['module',"list"];
	total_count_key = ['module','totalCount']
	page_size_count = 10

	items = [
		{
			"key":"itemName",
			"name":"商品描述",
			"width":700
		},
		{
			"key":"itemId",
			"name":"ID",
			"width":220
		},
		{
			"key":"price",
			"name":"价格",
			"width":220
		},
		{
			"key":"price",
			"name":"预计最低到手价",
			"width":220
		},
		{
			"key":"quantity",
			"name":"库存",
			"width":220
		}
	]
elif type_str == '4':
	current_page_string = 'pageNo'
	list_key = ['data',"data"];
	total_count_key = ['data','totalCount']
	page_size_count = 10

	items = [
		{
			"key":"base:activityId",
			"name":"活动编号",
			"width":700
		},
		{
			"key":"base:activityName",
			"name":"活动名称",
			"width":220
		},
		{
			"key":"price",
			"name":"活动详情",
			"width":220,
			"func":handle_type4_operation
		},
		{
			"key":"lowerPriceStr",
			"name":"预计最低到手价",
			"width":220,
			"func":handle_type4_operation
		},
		{
			"key":"quantity",
			"name":"库存",
			"width":220
		},
		{
			"key":"selected",
			"name":"操作",
			"width":220,
			"func":handle_type4_operation
		}
	]

elif type_str == '5':
	current_page_string = 'pageNo'
	list_key = ['data',"data"];
	total_count_key = ['data','totalCount']
	page_size_count = 10

	items = [
		{
			"key":"itemName",
			"name":"商品描述",
			"width":700
		},
		{
			"key":"itemId",
			"name":"ID",
			"width":220
		},
		{
			"key":"price",
			"name":"价格",
			"width":220,
			"func":handle_type4_operation
		},
		{
			"key":"lowerPriceStr",
			"name":"预计最低到手价",
			"width":220,
			"func":handle_type4_operation
		},
		{
			"key":"quantity",
			"name":"库存",
			"width":220
		},
		{
			"key":"selected",
			"name":"操作",
			"width":220,
			"func":handle_type4_operation
		}
	]
elif type_str == '6':
	current_page_string = 'currentPage'
	list_key = ['data','list'];
	total_count_key = ['data','total']
	page_size_count = 10

	items = [
		{
			"key":"itemName",
			"name":"商品",
			"width":700
		},
		{
			"key":"itemId",
			"name":"商品ID",
			"width":220
		},
		{
			"key":"juId",
			"name":"营销ID",
			"width":220,
		},
		{
			"key":"icStatusName",
			"name":"商品状态",
			"width":220,
		},
		{
			"key":"price",
			"name":"一口价",
			"width":220,
			"func":handle_type6_price
		},
		{
			"key":"price",
			"name":"专柜价",
			"width":220,
			"func":handle_type6_price
		},
		{
			"key":"lowestMarketPrice",
			"name":"最低标价",
			"width":220,
		},
		{
			"key":"activityPrice",
			"name":"活动价格",
			"width":220,
		},
		{
			"key":"dealPrice",
			"name":"预计普惠成交价",
			"width":220,
		},
		{
			"key":"statusName",
			"name":"活动状态",
			"width":220,
		},
        {
            "key":"depositPrice",
            "name":"定金",
            "width":220,
        }
	]
elif type_str == '7':
	current_page_string = 'page'
	list_key = ['data','data','data'];
	total_count_key = ['data','data','recordCount']
	page_size_count = 10

	items = [
		{
			"key":"item:title",
			"name":"商品名称",
			"width":700
		},
		{
			"key":"presaleOrdAmt:value",
			"name":"预售订单金额",
			"width":220
		},
		{
			"key":"sumPayDepositByrCnt:value",
			"name":"定金支付买家数",
			"width":220,
		},
		{
			"key":"presalePayItemCnt:value",
			"name":"定金支付件数",
			"width":220,
		},
		{
			"key":"sumPayDepositAmt:value",
			"name":"定金支付金额",
			"width":220,
		}
	]
elif type_str == '8':
	current_page_string = 'page'
	list_key = ['data','data'];
	total_count_key = ['data','recordCount']
	page_size_count = 10

	items = [
		{
			"key":"item:title",
			"name":"商品名称",
			"width":700
		},
		{
			"key":"item:itemNO",
			"name":"商品id",
			"width":220
		},
		{
			"key":"payAmt:value",
			"name":"支付金额",
			"width":220
		},
		{
			"key":"payAmt:cycleCrc",
			"name":"支付金额增长",
			"width":150,
			"func":handle_type8_cycleCrc
		},
		{
			"key":"payItmCnt:value",
			"name":"支付件数",
			"width":180,
		},
		{
			"key":"payItmCnt:cycleCrc",
			"name":"支付件数增长",
			"width":150,
			"func":handle_type8_cycleCrc
		},
		{
			"key":"sucRefundAmt:value",
			"name":"成功退款金额",
			"width":220,
		},
		{
			"key":"sucRefundAmt:cycleCrc",
			"name":"成功退款金额增长",
			"width":180,
			"func":handle_type8_cycleCrc
		},
		{
			"key":"itemCartCnt:value",
			"name":"商品加购件数",
			"width":180,
		},
		{
			"key":"itemCartCnt:cycleCrc",
			"name":"商品加购件数增长",
			"width":180,
			"func":handle_type8_cycleCrc
		},
		{
			"key":"itmUv:value",
			"name":"商品访客数",
			"width":180,
		},
		{
			"key":"itmUv:cycleCrc",
			"name":"商品访客数增长",
			"width":180,
			"func":handle_type8_cycleCrc
		}
	]

def getList():
	currentPage = 1
	totalPage = 1
	result = []
	cookie_array = cookie.replace(' ','').split(';')
	cookies = {}
	for i in cookie_array:
		index = i.find('=')
		if index>-1:
			cookies[i[:index]] = i[index+1:]

	while currentPage<=totalPage:
		print(f'正在请求第 {currentPage} 页 ')
		req_url = url

		if f'{current_page_string}=1' in url:
			req_url = url.replace(f'{current_page_string}=1',f'{current_page_string}={currentPage}')
		else:
			req_url = url.replace(f'{current_page_string}=2',f'{current_page_string}={currentPage}')
		r = requests.get(req_url,cookies=cookies)
		r = json.loads(r.text)
		new_list = r
		for i in list_key:
			new_list = new_list[i]
		result = result + new_list
		totalCount = r
		for i in total_count_key:
			totalCount = totalCount[i] 

		totalPage = math.ceil(totalCount/page_size_count)
		currentPage = currentPage + 1
	print(f'共{len(result)}条数据')
	return result


def write_excel(result):
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
	style.font = font # 设定样式

	# 边框
	borders = xlwt.Borders()
	borders.left = xlwt.Borders.THIN
	borders.right = xlwt.Borders.THIN
	borders.top = xlwt.Borders.THIN
	borders.bottom = xlwt.Borders.THIN
	style.borders = borders

	# 设置每行宽度
	for i in range(0,20):
		sheet1.col(i).width=220*20
		pass

	# 设置每行宽度
	for i in range(len(items)):
		item = items[i]
		sheet1.col(i).width=item['width']*20
		# 将数据插入第一行
		sheet1.write(0,i,item['name'],style)


	# 设置每行高度
	for x in range(0,5000):
		sheet1.row(x).height_mismatch = True
		sheet1.row(x).height=20*20

	for i in range(len(items)):
		item = items[i]
		# 将数据插入第一行
		sheet1.write(0,i,item['name'],style)

	font = xlwt.Font() # 为样式创建字体
	font.name = '微软雅黑' 
	font.bold = False
	style.font = font


	for i in range(0,len(result)):
		item = result[i]
	    # 设置每行宽度
		for m in range(len(items)):
			set_item = items[m]
			func = set_item.get('func')
			if func:
				# 带自定义函数的
				content = func(item,set_item['key'])
				sheet1.write(i+1,m,f'{content}',style)
			else:
				key = set_item['key']
				index = key.find(':')
				# 多级key
				if index > -1:
					keys = key.split(':')
					# content最开始等于item
					content = item
					for j in range(len(keys)):
						cur_key = keys[j]
						if isinstance(content,list):
							for n in range(len(content)):
								sheet1.write(i+1,m+n,content[n][cur_key],style)
						else:
							content = content.get(cur_key)
					if content is None:
						content = ''
					sheet1.write(i+1,m,f'{content}',style)

				else:
					content = item.get(set_item["key"]) if item.get(set_item["key"]) else ''
					sheet1.write(i+1,m,f'{content}',style)


	name = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d-%H%M%S')
	myxls.save(f'{os.path.expanduser("~")}/Desktop/{name}.xls')


def main():
	if len(items) <= 0:
		print('请配置列信息')
		return
	if len(list_key) <= 0:
		print('请配置list_key')
		return
	if len(total_count_key) <= 0:
		print('请配置total_count_key')
		return
	

	result = getList()
	write_excel(result)


main()





