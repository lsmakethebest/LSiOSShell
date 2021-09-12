
#!/usr/bin/env python3
#coding:utf-8

import sys
import os
import json

app_name = ''

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
		write_content += f'\n\nThread {index} name: {thread_name} {thread_queue}'
		return_line = '\n'
	write_content += f'{return_line}Thread {index}{crashed}:'

	line_number = 0

	for i in range(len(call_stacks)):
		stack = call_stacks[i]
		binary = all_binarys[stack['imageIndex']]
		binaryName = binary.get('name')
		if not binaryName:
			binaryName = '???'
		binary_start_address = all_binarys[stack['imageIndex']]['base']
		run_address = binary_start_address + stack['imageOffset']
		run_address_str = '0x{:016x}'.format(run_address)
		if stack.get('symbol'):
			write_content += f'\n{str(line_number).ljust(4)}{binaryName.ljust(30)}	{run_address_str} {stack.get("symbol")} + {stack["symbolLocation"]}'
		else:
			write_content += f'\n{str(line_number).ljust(4)}{binaryName.ljust(30)}	{run_address_str} {hex(binary_start_address)} + {stack["imageOffset"]}'
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
	write_content += f'\nCoalition:             {crash_info["parentProc"]} [{crash_info["coalitionID"]}]'

	write_content += f'\n\nDate/Time:             {crash_info["captureTime"]}'
	write_content += f'\nLaunch Time:           {crash_info["procLaunch"]}'
	write_content += f'\nOS Version:            {crash_info["osVersion"]["train"]} ({crash_info["osVersion"]["build"]})'
	write_content += f'\nRelease Type:          {crash_info["osVersion"]["releaseType"]}'
	write_content += f'\nBaseband Version:      {crash_info["basebandVersion"]}'
	write_content += f'\nReport Version:        104\n'
	

	write_content += f'\nException Type:        {crash_info["exception"]["type"]}'
	write_content += f'\nException Codes:       {crash_info.get("exception").get("code")}'
	write_content += f'\nsignal:                {crash_info["exception"]["signal"]}'
	write_content += f'\nsubtype:               {crash_info["exception"].get("subtype")}'

	vmRegionInfo = crash_info.get('vmRegionInfo')
	if vmRegionInfo:
		write_content += f'\vmRegionInfo: {vmRegionInfo}'		

	threads = crash_info['threads']
	thread_count = len(threads)

	triggered_thread = crash_info['faultingThread']

	write_content += f'\n\nTriggered by Thread:   {triggered_thread}'

	all_binarys = crash_info['usedImages']
	for i in range(thread_count):
		write_content = write_thread_content(i,triggered_thread,threads[i],write_content,all_binarys)

	write_content += f'\n\n'

	write_content += f'\nBinary Images:\n'

	all_binarys_content = []
	arch_type = ''
	for i in range(len(all_binarys)):
		binary = all_binarys[i]
		path = binary.get('path')
		address = binary["base"]
		address_str = '0x{:x}'.format(address)
		binary_name = binary.get('name')
		app_name = crash_info['procName']
		if not binary_name:
			binary_name = app_name

		if not path:
			path = crash_info['procPath']

		end_address = address + binary['size']
		uuid = binary['uuid'].replace('-','').lower()
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
		print('python dumpcrash2.py xxxxx.txt')
		exit(0)
	path = sys.argv[1]
	crash_header_info = get_crash__header_info(path)
	content = get_crash_content(path)
	write_file(content,path,crash_header_info)

main()


