
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

def write_file(content,file_path):
	write_content = ''
	crash_info = content['diagnosticMetaData']

	write_content += f'Incident Identifier:   {"00000000-0000-0000-0000-000000000000"}'
	write_content += f'\nHardware Model:        {crash_info["deviceType"]}'

	bundleIdentifier = crash_info.get("bundleIdentifier")
	write_content += f'\nIdentifier:            {bundleIdentifier}'

	write_content += f'\nVersion:               {crash_info["appBuildVersion"]} ({crash_info["appVersion"]})'
	write_content += f'\nCode Type:             {crash_info["platformArchitecture"]}'

	write_content += f'\nOS Version:            {crash_info["osVersion"]}'

	write_content += f'\n\nReport Version:        104\n'
	

	write_content += f'\nException Type:   {crash_info["exceptionType"]}'
	write_content += f'\nException Codes:  {crash_info["exceptionCode"]}'
	write_content += f'\nsignal:           {crash_info["signal"]}'
	write_content += f'\nTermination Description:    {crash_info["terminationReason"]}'



	call_stack_tree = content['callStackTree']
	call_stacks = call_stack_tree.get('callStacks')
	if not call_stacks:
		call_stacks = call_stack_tree['callStack']
	thread_count = len(call_stacks)

	triggered_thread = -1
	for i in range(thread_count):
		if call_stacks[i]['threadAttributed']:
			triggered_thread = i
			break

	write_content += f'\n\nTriggered by Thread:  {triggered_thread}'

	all_binarys = {}
	for i in range(thread_count):
		if len(call_stacks[i]['callStackRootFrames']) >1:
			print('write_file 出现异常无法解析，请查看数据格式修改脚本重新解析')
			exit(0)
		write_content = write_thread_content(i,triggered_thread,call_stacks[i]['callStackRootFrames'][0],write_content,all_binarys)

	write_content += f'\n\n'

	write_content += f'\nBinary Images:\n'

	all_binarys_content = []
	arch_type = crash_info['platformArchitecture']
	for key,value in all_binarys.items():
		address = int(value["startAddress"], 16)
		address = '0x{:x}'.format(address)
		uuid = value['uuid'].replace('-','').lower()
		end_address = address

		name = key
		if key == '???':
			name = app_name

		path = ''
		if key == '???' or key == app_name:
			path = f'/var/containers/Bundle/Application/xxx/{app_name}.app/{app_name}'

			if app_start_address and address == '0x0':
				address = app_start_address
				end_address = app_end_address
				uuid = app_uuid

			res = f'{address} - {end_address} {name} {arch_type}  <{uuid}> {path}'
			all_binarys_content.insert(0,res)
		else:
			path = fine_binary_path(key)
			res = f'{address} - {end_address} {name} {arch_type}  <{uuid}> {path}'
			all_binarys_content.append(res)

	write_content += "\n".join(all_binarys_content)
	write_content += "\n\nEOF\n\n"

	with open(file_path,'w') as file:
		file.write(write_content)


def write_thread_content(index,triggered_thread,content,write_content,all_binarys):
	crashed = " Crashed" if index == triggered_thread else ""
	write_content += f'\n\nThread {index}{crashed}:'
	line_number = 0
	write_content = write_thread_signal_stack(content,write_content,line_number,all_binarys)

	while content.get('subFrames'):
		
		if len(content['subFrames']) > 1:
			print('write_thread_content 出现异常无法解析，请查看数据格式修改脚本重新解析')
			exit(0)
		content = content['subFrames'][0]
		line_number += 1
		write_content = write_thread_signal_stack(content,write_content,line_number,all_binarys)
	return write_content

def write_thread_signal_stack(content,write_content,line_number,all_binarys):
	uuid = content['binaryUUID']
	binaryName = content.get('binaryName')
	binaryName = binaryName if binaryName else '???'
	binary_run_address = content['offsetIntoBinaryTextSegment']
	run_address = content['address']
	run_address = '0x{:016x}'.format(run_address)
	binary_start_address = '0x{:016x}'.format(binary_run_address)

	write_content += f'\n{str(line_number).ljust(4)}{binaryName.ljust(30)}	{run_address} {hex(binary_run_address)} + {content["address"]-binary_run_address}'
	all_binarys[binaryName] = {"name":binaryName,'uuid':uuid,'startAddress':binary_start_address}
	return write_content


def fine_binary_path(binary_name):
	device_support_path = os.path.expanduser('~') + '/Library/Developer/Xcode/iOS DeviceSupport'
	all_files = os.listdir(device_support_path)
	all_files.remove('.DS_Store')
	if len(all_files) == 0:
		print('本地无iOS DeviceSupport导致无法解析')
		exit(0)
	device = all_files[0]
	os.chdir(f"{device_support_path}/{device}/Symbols")
	result = os_popen(f'find . -name "{binary_name}"')
	return result[1:]


def main():
	if len(sys.argv) < 3:
		print('第一个参数 crash文件')
		print('第二个参数 machOName')
		print('第三个参数 app运行时 binary 基地址 可选参数')
		print('第四个参数 app运行时 binary 结束地址 可选参数')
		print('第五个参数 app binary uuid 可选参数')
		exit(0)
	path = sys.argv[1]

	if len(sys.argv) > 3:
		global app_start_address
		global app_end_address
		global app_uuid

		app_start_address = sys.argv[3]
		app_end_address = sys.argv[4]
		app_uuid = sys.argv[5]

	result = load_json(path)
	start_time = result['timeStampBegin'].replace(':',"_")
	end_time = result['timeStampEnd'].replace(':',"_")
	global app_name
	app_name = sys.argv[2]

	file_path = os.path.expanduser('~')+ f'/Desktop/DiagnosticPayloads/{app_name}/{start_time}-{end_time}'
	if not os.path.exists(file_path):
		os.makedirs(file_path) 

	list_count = len(result['crashDiagnostics'])

	for i in range(list_count):
		content = result['crashDiagnostics'][i]
		write_file(content,f'{file_path}/{i}.txt')

main()


