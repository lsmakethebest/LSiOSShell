#!/usr/bin/env python
#coding: UTF-8

import os
import sys
import shutil
import time
import re
import json


def show_files(path, all_files):
	# 首先遍历当前目录所有文件及文件夹
	file_list = os.listdir(path)
	# 准备循环判断每个元素是否是文件夹还是文件，是文件的话，把名称传入list，是文件夹的话，递归
	for file in file_list:
		# 利用os.path.join()方法取得路径全名，并存入cur_path变量，否则每次只能遍历一层目录
		cur_path = os.path.join(path, file)
		# 判断是否是文件夹
		if os.path.isdir(cur_path):
			show_files(cur_path, all_files)
		else:
			if file.endswith(".js") or file.endswith(".jsx") or file.endswith(".css"):
				all_files.append(cur_path)

	return all_files


def findPicture(filePath):
	# /Users/liusong/Desktop/amap/1060_行中pro/amap_bundle_routecommute/ajx_modules/amap_bundle_lib_drivecommon/src/routecommute/overlay/BubbleTipJamDetail.js
	with open(filePath,"r") as f:
			picList = []
			text = f.read()

			# u = r'require\.toUrl\((\'|\")(?!amap_bundle_).+\.(webp|png)'
			u = re.compile(r'require\.toUrl\([\'"](?!amap_bundle_).+\.webp')
			res = re.findall(u,text)
			
			for name in res:
				if name and "@amap_bundle_" not in name:
					name= name[15:]
					picList.append(name)

			u = re.compile(r'require\.toUrl\([\'"](?!amap_bundle_).+\.png')
			res = re.findall(u,text)
			for name in res:
				if name and "@amap_bundle_" not in name:
					name= name[15:]
					picList.append(name)

			u = re.compile(r'require\.toUrl\([\'"](?!amap_bundle_).+\.gif')
			res = re.findall(u,text)
			for name in res:
				if name and "@amap_bundle_" not in name:
					name= name[15:]
					picList.append(name)

			u = re.compile(r'require\.toUrl\([\'"](?!amap_bundle_).+\.zip')
			res = re.findall(u,text)
			for name in res:
				if name and "@amap_bundle_" not in name:
					name= name[15:]
					picList.append(name)


			return picList


def main():
	contents = show_files(sys.argv[1], [])
	# 传入空的list接收文件名

	# 循环打印show_files函数返回的文件名列表
	# print(len(contents))
	totalPicList = []
	for content in contents:
		# print(content)
		picList = findPicture(content)
		for pic in picList:
			if pic not in totalPicList:
				totalPicList.append(pic)
	# print(totalPicList)
	json_str = json.dumps(totalPicList)# 再转化为json的字符串形式
	file = open(sys.argv[1] + '/result.txt', 'w')
	file.write(json_str)
	file.close()
	print(len(totalPicList))



main()




