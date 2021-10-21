
#!/usr/bin/env python3
#coding:utf-8

import sys
import os
import json

app_name = ''
app_start_address = ''
app_end_address = ''
app_uuid = ''

def os_popen(cmd):
    # 执行 os.system(cmd)，返回执行结果
    return os.popen(cmd).read().replace('\n','')

# 加载本地json文件，返回为对象
def load_json(path):
    if not os.path.exists(path):
        print(f'load json 失败：{path} 不存在')
    with open(path) as f:
        return json.load(f)

def write_thread_content(index,triggered_thread,thread,write_content,all_binarys):
	crashed = " Crashed" if index == triggered_thread else ""
	call_stacks = thread['frames']
	thread_name = thread.get("name") 
	thread_queue= thread.get("queue")
	if not thread_queue:
		thread_queue = ''

	return_line = '\n\n'
	if thread_name or thread_queue:
		if thread_queue:
			thread_queue = f'Dispatch queue:{thread_queue}'
		write_content += f'\n\nThread {index} name: {thread_name} {thread_queue}'
		return_line = '\n'
	write_content += f'{return_line}Thread {index}{crashed}:'

	line_number = 0

	for i in range(len(call_stacks)):
		stack = call_stacks[i]
		binaryName = ''
		imageIndex = -1
		imageOffset = 0
		binary_start_address = 0
		run_address_str = ''
		if isinstance(stack,list):
			imageIndex = stack[0]
			imageOffset = stack[1]
		else:
			imageIndex = stack['imageIndex']
			imageOffset = stack['imageOffset']

		binary = all_binarys[imageIndex]
		binaryName = binary.get('name')
		binary_start_address = all_binarys[imageIndex]['base']
		run_address = binary_start_address + imageOffset
		run_address_str = '0x{:016x}'.format(run_address)

		if not binaryName:
			binaryName = '???'
		
		if not isinstance(stack,list) and stack.get('symbol'):
			write_content += f'\n{str(line_number).ljust(4)}{binaryName.ljust(30)}	{run_address_str} {stack.get("symbol")} + {stack["symbolLocation"]}'
		else:
			write_content += f'\n{str(line_number).ljust(4)}{binaryName.ljust(30)}	{run_address_str} {hex(binary_start_address)} + {imageOffset}'
		line_number += 1
	return write_content

def get_crash__header_info(path):
	with open(path, 'r', encoding='utf-8') as f:  # 打开文件
		lines = f.readlines()  # 读取所有行
		first_line = lines[0]  # 取第一行
		return first_line

def get_crash_content(path):
	lines = open(path, 'r').readlines()
	del lines[0]
	content = json.loads(''.join(lines))
	return content

def write_file(crash_info,file_path,crash_header_info):
	write_content = ''
	
	write_content += f'Incident Identifier:   {crash_info["incident"]}'
	write_content += f'\nCrashReporter Key:     {crash_info["crashReporterKey"]}'

	write_content += f'\nHardware Model:        {crash_info["modelCode"]}'
	write_content += f'\nProcess:               {crash_info["procName"]}'
	write_content += f'\nPath:                  {crash_info["procPath"]}'
	write_content += f'\nIdentifier:            {crash_info["coalitionName"]}'
	write_content += f'\nVersion:               {crash_info["bundleInfo"]["CFBundleVersion"]} ({crash_info["bundleInfo"]["CFBundleShortVersionString"]})'
	
	write_content += f'\nCode Type:             {crash_info["cpuType"]}'
	write_content += f'\nRole:                  {crash_info["procRole"]}'
	write_content += f'\nParent Process:        {crash_info["parentProc"]}'
	write_content += f'\nCoalition:             {crash_info["coalitionName"]} [{crash_info["coalitionID"]}]'

	write_content += f'\n\nDate/Time:             {crash_info["captureTime"]}'
	write_content += f'\nLaunch Time:           {crash_info["procLaunch"]}'
	write_content += f'\nOS Version:            {crash_info["osVersion"]["train"]} ({crash_info["osVersion"]["build"]})'
	write_content += f'\nRelease Type:          {crash_info["osVersion"]["releaseType"]}'
	write_content += f'\nBaseband Version:      {crash_info["basebandVersion"]}'
	write_content += f'\nReport Version:        104\n'
	

	write_content += f'\nException Type:        {crash_info["exception"]["type"]}'
	write_content += f'\nException Codes:       {crash_info.get("exception").get("codes")}'
	write_content += f'\nsignal:                {crash_info["exception"]["signal"]}'
	subtype = crash_info["exception"].get("subtype")
	if subtype:
		write_content += f'\nsubtype:               {subtype}'

	vmRegionInfo = crash_info.get('vmregioninfo')
	if vmRegionInfo:
		write_content += f'\nvmRegionInfo: {vmRegionInfo}'		

	threads = crash_info['threads']
	thread_count = len(threads)

	triggered_thread = crash_info.get('faultingThread')
	if not triggered_thread:
		for i in range(thread_count):
			if threads[i].get('triggered'):
				triggered_thread = i
				break

	write_content += f'\n\nTriggered by Thread:   {triggered_thread}'

	all_binarys = []

	# 15以下系统此参数有值
	imageExtraInfo = crash_info['legacyInfo'].get('imageExtraInfo')
	if imageExtraInfo:
		all_binarys = imageExtraInfo
		usedImages = crash_info['usedImages']
		for i in range(len(all_binarys)):
			binary = all_binarys[i]
			binary['uuid'] = usedImages[i][0]
			binary['base'] = usedImages[i][1]
			binary['source'] = usedImages[i][2]
	else:
		all_binarys = crash_info['usedImages']

	lastExceptionBacktrace = crash_info.get("lastExceptionBacktrace")
	if lastExceptionBacktrace:
		write_content += f'\n\nLast Exception Backtrace:'
		if isinstance(lastExceptionBacktrace,list):
			content = '('
			for i in range(len(lastExceptionBacktrace)):
				backtrace = lastExceptionBacktrace[i]
				address = all_binarys[backtrace['imageIndex']]['base']	+ backtrace['imageOffset']
				space = " "
				if i == 0:
					space = ""
					pass
				content += f'{space}{hex(address)}'
			content += ")"
			write_content += f'\n{content}'
		else:
			write_content += f'\n{lastExceptionBacktrace}'
	
	for i in range(thread_count):
		write_content = write_thread_content(i,triggered_thread,threads[i],write_content,all_binarys)


# Thread 129 crashed with ARM Thread State (64-bit):
# x0: 0x0000000000000000   x1: 0x0000000000000000   x2: 0x0000000000000000   x3: 0x0000000000000000
# x4: 0x0000000000000000   x5: 0x0000000000000000   x6: 0x0000000000000000   x7: 0x0000000000000000
# x8: 0xf68be07968b68437   x9: 0xf68be07a64757437  x10: 0x0000000061987653  x11: 0x0000000000000000
# x12: 0x0000000000000030  x13: 0xffffffffffffffff  x14: 0x0000000000000031  x15: 0x0000000000000030
# x16: 0x0000000000000148  x17: 0x000000030cc3f000  x18: 0x0000000000000000  x19: 0x0000000000000006
# x20: 0x000000000003120f  x21: 0x000000030cc3f0e0  x22: 0x000000030cc3bfa8  x23: 0x000000011966791c
# x24: 0x000000030cc3c7f0  x25: 0x0000000000000000  x26: 0x0000000000000001  x27: 0xaaaaaaaaaaaaaaab
# x28: 0x0000000305f5a408   fp: 0x000000030cc3b280   lr: 0x00000001d3721a9c
# sp: 0x000000030cc3b260   pc: 0x00000001b5c9d334 cpsr: 0x40000000
# esr: 0x56000080  Address size fault

	thread_state = crash_info['threads'][triggered_thread].get("threadState")
	if not thread_state:
		thread_state = crash_info.get('threadState')
	if thread_state:
		write_content += f'\n\nThread {triggered_thread} crashed with {thread_state.get("flavor")}:'
		thread_state_content = []

		thread_state_x = thread_state['x']
		for i in range(len(thread_state_x)):
			thread_state_x_index = thread_state_x[i]
			value = ''
			if isinstance(thread_state_x_index,int):
				value = thread_state_x_index
			else:
				value = thread_state_x_index.get("value")
			address = '0x{:016x}'.format(value)
			thread_state_content.append(f'x{i}: {address}')
			

		for key in thread_state:
			if key == 'x' or key == 'flavor':
				continue
			thread_state_value = thread_state[key]
			value = ''
			if isinstance(thread_state[key],dict):
				value = thread_state_value["value"]
			else:
				value = thread_state_value

			address = ''
			if isinstance(value,int):
				address = '0x{:016x}'.format(value)
			else:
				address = value
			thread_state_content.append(f'{key}: {address}')
		thread_state_content_str = ''
		for i in range(len(thread_state_content)):
			thread_state_content_str += thread_state_content[i].ljust(25)
			if i+1>0 and (i+1)%4 == 0:
				thread_state_content_str += '\n'
		write_content += f'\n{thread_state_content_str}'

	write_content += f'\n\n\nBinary Images:\n'

	all_binarys_content = []
	arch_type = ''
	for i in range(len(all_binarys)):
		binary = all_binarys[i]
		path = binary.get('path')
		address = binary["base"]
		binary_name = binary.get('name')
		app_name = crash_info['procName']
		if not binary_name:
			binary_name = app_name

		if not path:
			path = crash_info['procPath']

		end_address = address + binary['size']
		uuid = binary['uuid'].replace('-','').lower()


		if app_start_address and address == 0:
			address = int(app_start_address,16)
			end_address = int(app_end_address,16)
			uuid = app_uuid

		if binary.get('arch'):
			arch_type = binary['arch']
		res = f'{hex(address)} - {hex(end_address)} {binary_name} {arch_type}  <{uuid}> {path}'
		is_app_stack = False
		if path and app_name in path:
			is_app_stack = True

		if is_app_stack:
			all_binarys_content.insert(0,res)
		else:
			all_binarys_content.append(res)

	write_content += "\n".join(all_binarys_content)
	write_content += "\n\nEOF\n\n"
	write_content = crash_header_info + write_content

	with open(file_path+'.txt','w') as file:
		file.write(write_content)


def main():
	if len(sys.argv) < 2:
		print('第一个参数 crash文件')
		print('第二个参数 app运行时 binary 基地址 可选参数')
		print('第三个参数 app运行时 binary 结束地址 可选参数')
		print('第四个参数 app binary uuid 可选参数')
		exit(0)
	path = sys.argv[1]
	if len(sys.argv) > 2:
		global app_start_address
		global app_end_address
		global app_uuid
		app_start_address = sys.argv[2]
		app_end_address = sys.argv[3]
		app_uuid = sys.argv[4]
	crash_header_info = get_crash__header_info(path)
	content = get_crash_content(path)
	write_file(content,path,crash_header_info)
	print(f'生成新文件 {path}.txt')

main()
