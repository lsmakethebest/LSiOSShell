#!/usr/bin/env python
#coding: UTF-8

import os
import sys
import shutil
import time

# 用法一解析crash
# 参数1 carsh文件
# 参数2 dsym文件目录(此参数可选，如果不传参则会先从本机查找符合条件的dsym)
# python dump_system_symbol.py xxxxx.carsh dsym文件目录


# 用法二解析指定行（适用于日志错乱的时候，只有runAddress）
# 参数1 carsh文件
# 参数2 13:22 代表修改13行到22行（不包括22行）中仅有运行地址但没有loadAddress的符号化
# python dump_system_symbol.py xxxxx.carsh 13:22

crash_file = sys.argv[1]
device_support_path = ''
search_device_support = False
new_file_path = crash_file + '.txt'
process_name = ''
os_version = ''
dysm_file = ''

if len(sys.argv) > 2:
	dysm_file = sys.argv[2]

def get_all_symbol_address(filePath):
	start = False
	end = False
	lineNumner = 0
	dic = {}
	lastExceptionStart = False
	with open(filePath) as file:
		for line in file:
			originalLine = line
			lineNumner = lineNumner + 1;

			if 'Last Exception Backtrace:' in line:
				lastExceptionStart = True
				start = True

			if 'Thread 0' in line:
				lastExceptionStart = False
				start = True

			if start == False or end == True:
				continue

			if start == True and ('Binary Images:' in line or 'Thread State' in line):
				end = True
				continue

			# Last Exception Backtrace: 调用栈 0行不需-1，其他行需-1，其实就是最后执行的frame 不需要-1
			index = line.find('0x');
			if index  == -1:
				continue

			runModeAddressIndex = originalLine.find('0x',index+1)
			isDumped = runModeAddressIndex == -1
			if isDumped:
				continue

			writeBeforeContent = originalLine[:runModeAddressIndex]

			runAddress = line[index:runModeAddressIndex-1]
			runModeAddress = originalLine[runModeAddressIndex:runModeAddressIndex+11]

			if lastExceptionStart and line[0] != '0':
				runAddress = int(runAddress, 16) - 1
				runAddress = str(hex(runAddress))

			newLine = originalLine[4:]
			newLine = newLine.replace(' ','');
			newLine = newLine.replace('\t','');
			newLine = newLine.replace('\n','');
			index = newLine.find('0x');
			modeName = newLine[:index]

			if dic.get(modeName) is None:
				dic[modeName] = {}

			modeDic = dic.get(modeName)

			curLoadAddress = modeDic.get('loadAddress')
			if curLoadAddress is None or runModeAddress != curLoadAddress and len(runModeAddress) == 11:
				modeDic['loadAddress'] = runModeAddress

			addressList = modeDic.get('addressList')

			if addressList is None:
				modeDic['addressList'] = []

			addressList = modeDic.get('addressList')
		    # 行号从0开始
			addressList.append({'address':runAddress,
				'line':str(lineNumner-1),
				'beforeContent':writeBeforeContent
				}
			) 
	return dic


# 获取系统符号目录
def get_all_symbol_path(filePath):
	start = False
	# 字典可以避免重复项，有的会出现多次
	dic = {}
	lineNumner = 0
	with open(filePath,'r') as fd:
		for line in fd:
			lineNumner = lineNumner + 1
			if 'Binary Images:' in line:
				start = True
				continue
			if start == False:
				continue

			if '>' not in line:
				continue

			line = line.replace('\n','')
			index = line.find('0x')
			if index < 0:
				continue

			endAddressIndex = line.find('0x',index+11)
			if endAddressIndex < 0:
				continue

			newLine = line[endAddressIndex+11:]
			newLine.lstrip()

			mdoeNameEndIndex = newLine.find('arm')
			modeName = newLine[:mdoeNameEndIndex - 1].replace(' ','')
			index = line.find('>')
			path = line[index + 2:]

			if dic.get(modeName) is None:
				dic[modeName] = {}

			modeDic = dic.get(modeName)
			arch = newLine[mdoeNameEndIndex:newLine.find('>')-32-3]
			modeDic['path'] = path
			# uuid：ddb9e29650f4345b950f3ca65ed4f35a
			modeDic['uuid'] = line[index-32:index]
			modeDic['arch'] = arch

			# 0x1a0ccb000 -        0x1a0d21fff  Accounts arm64e
			# 0x10ad8c000 - 0x10adf3fff dyld arm64e  <e008b93875933f57b94a747bc6c3beb5> /usr/lib/dyld
			startIndex = line.find('0x')
			startAddress = line[startIndex:startIndex + 11]
			endIndex = line.find('0x',startIndex + 11)
			endAddress = line[endIndex:endIndex + 11]
			if startAddress[-2:] != '00' or endAddress[-2:] != 'ff':
				print(modeName + ': startAddress或endAddress地址无效,错误发生在第 ' + str(lineNumner) + ' 行')
				continue

			modeDic['startAddress'] = startAddress
			modeDic['endAddress'] = endAddress
			# print(modeName + ':' + startAddress + '-' + endAddress)
	return dic

# 符号化地址
def atos_all_symbol(filePath,modeList,stackModeList):
	ms = open(filePath ,'r')
	lines = ms.readlines()
	ms.close()
	for x in stackModeList:
		modeName = x
		modeDic = modeList.get(modeName)
		if modeDic is None:
			lineNumner = str(int(stackModeList.get(modeName).get('addressList')[0].get('line')) + 1)
			print('正在符号化: 【' + modeName + '】 error:未找到对应的符号目录,自动跳过此项 => 错误可能发生在第【' + lineNumner + '】行')
			continue

		modePath = modeDic.get('path')
		arch_type = modeList.get(modeName).get('arch')
		if modePath is None:
			print('not match binary path ,resaon:日志错乱')
			continue

		uuid = modeList.get(modeName).get('uuid')

		isApp = False

		global process_name
		global dysm_file
		if modeName == process_name:
			isApp = True
			# 未传参数，先本地查找
			if dysm_file == '':
				print('正在查找电脑上符号条件的DSYM 【{}】'.format(uuid))
				dysm_file = find_match_dsym(uuid)
				if dysm_file != '':
					print('查找到符号条件的DSYM: ' + dysm_file)
				else:
					print('未查找到符号条件的DSYM')
			# 没传参数而且本机没找到符合条件的
			if dysm_file == '':
				print('正在符号化: 【' + modeName + '】 error:符号化需提供DSYM文件,请传参数2:DSYM文件目录')
				continue

		if modeName != process_name and '/var' in modePath:
			print('正在符号化: 【' + modeName + '】 error：非系统库，属于三方库')
			continue
		dic = stackModeList.get(x)
		runModeAddress = dic.get('loadAddress')
		addressList = dic.get('addressList')
		allAddressList = []
		for y in addressList:
			allAddressList.append(y.get('address'))

		allAddressStr = ' '.join(allAddressList)

		global search_device_support
		global device_support_path
		global os_version

		if search_device_support == False:
			search_device_support = True
			device_support_path = find_device_support_path(os_version,uuid,modePath)

		if device_support_path == '' and isApp == False:
			print('not match device_support_path for ' + modeName)
			continue

		machO_path = '{}/Symbols'.format(device_support_path) + modePath
		if isApp:
			machO_path = '{}/Contents/Resources/DWARF/{}'.format(dysm_file,process_name) 
		if checkUUID(uuid,machO_path) == False:
			print(modeName + '[' + uuid + ']' + ' 和 ' + machO_path + ' uuid不匹配')
			continue
		print('正在符号化: 【' + modeName + '】  共【' + str(len(allAddressList)) + '】个symbol')
		command = 'atos -arch ' + arch_type + ' -o ' + '\'{}\''.format(machO_path) + ' -l ' + runModeAddress + ' ' + allAddressStr
		result = os.popen(command).read()
		result = result.split('\n')
		length = len(allAddressList)
		for i in range(length):
			content = result[i]
			line = addressList[i].get('line')
			if '0x' in content:
				lineNumner = str(int(line) + 1)
				print(modeName + ': 【' + allAddressList[i] + '】符号化失败,位于carsh文件 第:' + lineNumner + '行')

			beforeContent = addressList[i].get('beforeContent')
			content = beforeContent + content + '\n'
			# 去除无用显示( in CoreFoundation)
			content = content.replace('(in '+ modeName + ') ','')
			lines.pop(int(line))
			lines.insert(int(line),content)

	s = ''.join(lines)
	fp = open(new_file_path, 'w')
	fp.write(s)
	fp.close()

def checkUUID(uuid,machO_path):
	# print('uuid:' + uuid + ' path:' +  machO_path)
	result = os.popen('/usr/bin/symbols -uuid' + ' \'{}\''.format(machO_path)).read()
	result = result.replace('\n','').replace('-','').lower()

	check = False
	if uuid in result:
		check = True
		return check
	return check

def find_device_support_path(os_version,uuid,machO_path):
	path = os.path.expanduser('~') + '/Library/Developer/Xcode/iOS DeviceSupport/'
	f_list = os.listdir(path)
	for l in f_list:
		if os_version in l:
			new_path = path + l + '/Symbols' + machO_path
			if checkUUID(uuid,new_path):
				device_support_path = path + l
				print('match device_support => ' + device_support_path)
				return path + l
	print('not match device_support')
	print("如需解析，请下载系统符号，可以使用：https://github.com/lsmakethebest/LSiOSShell/fetchDeviceSupport.sh")
	return ''

def find_match_dsym(uuid):
	# B1E8395F-0ECB-36FE-A110-73FECFA46012
	# 转换成指定格式
	uuid = uuid.upper()
	uuid = uuid[:8] + '-' + uuid[8:12] + '-' + uuid[12:16] + '-' + uuid[16:20] + '-' + uuid[20:]
	result = os.popen('mdfind com_apple_xcode_dsym_uuids=' + uuid).read()
	if result == '':
		return ''

	list = result.split('\n')
	return list[0]

def get_process_name(filePath):
	with open(filePath,'r') as fd:
		for line in fd:
			# Process:             AMapiPhone [30284]
			if 'Process:' in line:
				tempLine = line.replace(' ','')
				process_name = tempLine[8:tempLine.find('[')]
				return process_name
	return ''

def get_os_version(filePath):
	with open(filePath,'r') as fd:
		for line in fd:
			#OS Version:          iPhone OS 13.3.1 (17D50)
			#OS Version:      iPhone OS 13.2 (17B84)
			if 'OS Version:' in line and os_version == '':
				return line[line.find('OS',11)+3:].rstrip()
	return ''


def atos_crash(filePath):
	modeList = get_all_symbol_path(filePath)
	stackModeList = get_all_symbol_address(filePath)
	atos_all_symbol(filePath,modeList,stackModeList)

def symbolicatecrash(filePath):
	global dysm_file
	if dysm_file == '':
		modeList = get_all_symbol_path(filePath)
		uuid = modeList.get(process_name).get('uuid')
		print('正在查找符合条件的DSYM 【{}】'.format(uuid))
		dysm_file = find_match_dsym(uuid)
		if dysm_file != '':
			print('查找到符号条件的DSYM {}'.format(dysm_file))
		else:
			print('未查找到符号条件的DSYM,退出')
			exit()
	print('开始使用系统symbolicatecrash工具符号化...')
	prePath = '/Applications/Xcode.app/Contents/SharedFrameworks/DVTFoundation.framework/Versions/A/Resources'
	os.chdir(prePath)
	command = 'export DEVELOPER_DIR=\"/Applications/XCode.app/Contents/Developer\" && ' +'./symbolicatecrash {} {} > {}'.format(filePath,dysm_file,new_file_path)
	result = os.popen('{}'.format(command)).read()
	if result:
		print(result)


def dump_crash():
	start_t = time.time()
	symbolicatecrash(crash_file)
	stackModeList = get_all_symbol_address(new_file_path)
	length = len(stackModeList)
	if length > 0:	
		print('还有 {} 个二进制模块未符号化'.format(length))
		print('开始使用atos符号化')
		atos_crash(new_file_path)

	end_t = time.time()
	print('新文件目录: ' + new_file_path)
	print('耗时: ' + str(end_t-start_t) + ' 秒')

def get_runAddress_noLoadAddress(filePath,startLineNumber,endLineNumber):
	start = False
	end = False
	lineNumner = 0
	list = []
	lastExceptionStart = False
	with open(filePath) as file:
		for line in file:
			originalLine = line
			lineNumner = lineNumner + 1;
			line = line.replace('\n','')
			if 'Last Exception Backtrace:' in line:
				lastExceptionStart = True
				start = True

			if 'Thread 0' in line:
				lastExceptionStart = False
				start = True

			if 'Exception Codes' in line:
				continue

			if lineNumner >= int(startLineNumber) and lineNumner < int(endLineNumber):
				# Last Exception Backtrace: 调用栈 0行不需-1，其他行需-1，其实就是最后执行的frame 不需要-1
				index = line.find('0x');
				if index  == -1:
					continue

				runAddressEndIndex = originalLine.find(' ',index+1)
				runAddress = line[index:runAddressEndIndex]

				originalAddress = runAddress
				if lastExceptionStart and line[0] != '0':
					runAddress = int(runAddress, 16) - 1
					runAddress = str(hex(runAddress))

				# 行号从0开始
				list.append(
					{
						'address':runAddress,
						'line':str(lineNumner-1),
						'originalAddress': originalAddress
					}
				) 
	return list


def dump_single_address(filePath,startLineNumber,endLineNumber):
	ms = open(filePath ,'r')
	lines = ms.readlines()
	ms.close()

	list = get_all_symbol_path(filePath)
	stackModeList = get_runAddress_noLoadAddress(filePath,startLineNumber,endLineNumber)
	for addressDic in stackModeList:
		for x in list:
			dic = list.get(x)
			startAddress = list.get(x).get('startAddress')
			endAddress = list.get(x).get('endAddress')
			if startAddress is None or endAddress is None:
				continue
			if 'var' in  dic.get('path'):
				# print('三方库无法符号化')
				continue

			start = int(startAddress,16)
			end = int(endAddress,16)
			address = addressDic.get('address')
			addressInt = int(address,16)
			global device_support_path
			global os_version
			if addressInt >= start and addressInt < end:
				if x == process_name:
					# print('app符号不处理')
					continue
				if device_support_path == '':
					device_support_path = find_device_support_path(os_version,dic.get('uuid'),dic.get('path'))
				if device_support_path == '':
					print('not match device_support_path and exit')
					exit()
				machO_path = '{}/Symbols'.format(device_support_path) + dic.get('path')
				command = 'atos -arch ' + dic.get('arch') + ' -o ' + '\'{}\''.format(machO_path) + ' -l ' + dic.get('startAddress') + ' ' + address
				result = os.popen(command).read().replace('\n','')
				# print(address + ' => ' + result)
				line = lines[int(addressDic.get('line'))]
				originalAddress = addressDic.get('originalAddress')
				newContent = originalAddress + ' ' + result
				if line.find(newContent) == -1:
					line = line.replace(originalAddress,newContent)
					lines[int(addressDic.get('line'))] = line
					break
	s = ''.join(lines)
	fp = open(filePath, 'w')
	fp.write(s)
	fp.close()

def main():
	global os_version
	os_version = get_os_version(crash_file)
	global process_name
	process_name =  get_process_name(crash_file)
	if dysm_file != '' and len(dysm_file) < 10:
		dump_single_address(crash_file,dysm_file.split(':')[0],dysm_file.split(':')[1])
	else:
		dump_crash()

main()

