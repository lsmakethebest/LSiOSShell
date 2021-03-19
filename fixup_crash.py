
#!/usr/bin/env python3
#coding:utf-8

import sys
import os
import json

crash_file = sys.argv[1]


def get_binary_arch_type(crash_info):
	arch_type = ''
	binary_images = crash_info['legacyInfo']['imageExtraInfo']
	for i in range(len(binary_images)):
		arch_type = binary_images[i].get('arch')
		if arch_type:
			return arch_type


def get_thread_state_content(crash_info):
	thread_state = crash_info['threadState']
	crash_index = str(crash_info['legacyInfo']['threadTriggered']['index'])

	flavor = thread_state["flavor"]
	flavor = flavor.replace('_',' ')
	thread_state_content = f'Thread {crash_index} crashed with {flavor }:\n'

	x_list = thread_state.get('x')
	length = 0
	state_list = []
	for i in range(0,len(x_list),4):
		for j in range(4):
			if i+j < len(x_list):
				x0 = 'x' + str(i+j)
				x0 = x0.rjust(5)
				address = x_list[i+j]
				address = '0x' + hex(address).replace('0x','').zfill(16)
				content = f'{x0}: {address}'
				state_list.append(content)

	for key in thread_state:
		if key != 'x' and  key != 'flavor' and 'esr' not in key:
				key_content = key.rjust(5)
				address = thread_state[key]
				address = '0x' + hex(address).replace('0x','').zfill(16)
				content = f'{key_content}: {address}'
				state_list.append(content)


	for i in range(0,len(state_list),4):
		content = ' '
		for j in range(4):
			if i+j < len(state_list):
				content = f'{content}{state_list[i+j]}'
		content = content + '\n'
		thread_state_content = thread_state_content + content

	key = 'esr'
	key_content = key.rjust(5)
	address = thread_state[key]
	address = '0x' + hex(address).replace('0x','').zfill(16)
	content = f' {key_content}: {address} {thread_state["esr_description"]}\n\n'

	thread_state_content = thread_state_content + content
	return thread_state_content


def get_binary_image_content(crash_info,crash_head_info,max_address):
	binary_image_content = ''
	binary_images = crash_info['usedImages']
	for i in range(len(binary_images)):
		binary_image = binary_images[i]
		binary_image_name = crash_info['legacyInfo']['imageExtraInfo'][i].get('name')
		binary_image_path = crash_info['legacyInfo']['imageExtraInfo'][i].get('path')
		binary_image_arch = crash_info['legacyInfo']['imageExtraInfo'][i].get('arch')
		binary_image_uuid = binary_image[0].replace('-','')
		if binary_image_uuid == '00000000000000000000000000000000':
			binary_image_uuid = crash_head_info['slice_uuid'].replace('-','')

		binary_image_start_address = binary_image[1]
		binary_image_end_address = binary_image_start_address + crash_info['legacyInfo']['imageExtraInfo'][i].get('size') - 1
		# 对于段重排的app获取地址为0
		if binary_image_start_address == 0:
			binary_image_end_address = max_address

		# 对于段重排的app获取name为空
		if not binary_image_name:
			binary_image_name = crash_info['procName']
			binary_image_arch = get_binary_arch_type(crash_info)
			binary_image_path = crash_info['procPath']

		# 是app的话放到最前面
		if binary_image_name == crash_info['procName']:
			binary_image_content = f'{str(hex(binary_image_start_address))} - {str(hex(binary_image_end_address))} {binary_image_name} {binary_image_arch} <{binary_image_uuid}> {binary_image_path}\n{binary_image_content}'
		else:
			binary_image_content = f'{binary_image_content}{str(hex(binary_image_start_address))} - {str(hex(binary_image_end_address))} {binary_image_name} {binary_image_arch} <{binary_image_uuid}> {binary_image_path}\n'

	return binary_image_content


def get_thread_content(crash_info):
	max_address = 0
	thread_all_content = ''
	threads = crash_info['threads']
	for i in range(len(threads)):
		thread  = threads[i]
		thread_content = ''
		queue = thread.get("queue")
		if not queue:
			queue = ''
		else:
			queue = '  Dispatch queue: ' + queue

		thread_name = thread.get("name")
		if not thread_name:
			thread_name = ''
		else:
			thread_name = '  ' + thread_name

		triggered = thread.get('triggered')
		if triggered:
			 triggered = ' Crashed'
		else:
			triggered = ''
		if thread_name or queue:
			thread_content = f'{thread_content}Thread {i} name:{thread_name}{queue}\n'
		else:
			thread_name = ''
		thread_content = f'{thread_content}Thread {i}{triggered}:\n'

		frames = thread['frames']

		for j in range(len(frames)):
			frame = frames[j]
			binary_index = frame[0]
			binary_name = crash_info['legacyInfo']['imageExtraInfo'][binary_index].get('name')
			if not binary_name:
				binary_name = '???'

			symbol_offset = frame[1]
			static_address_number = crash_info['usedImages'][binary_index][1]

			if binary_name == crash_info['procName'] or binary_name == '???':
				max_address = max(max_address,static_address_number+symbol_offset)

			run_start_address = str(hex(static_address_number))
			run_address = '0x' + str(hex(static_address_number+symbol_offset)).replace('0x','').zfill(16)
			if run_start_address == '0x0':
				run_start_address = '0'
			thread_content = f'{thread_content}{str(j).ljust(4)}{binary_name.ljust(30)}	{run_address} {run_start_address} + {str(symbol_offset)}\n'
		thread_all_content = thread_all_content + thread_content + '\n'

	return (thread_all_content,max_address)

def get_aslr_address(crash_info):
	arch_type = get_binary_arch_type(crash_info)
	os_version = crash_info['osVersion']['train'].replace(' ','')
	device_support_path = ''
	if arch_type != 'arm64e':
		arch_type = ''
	else:
		arch_type = f' {arch_type}'
	if 'iPhoneOS' in os_version:
		device_support_path = f'~/Library/Developer/Xcode/iOS DeviceSupport/{os_version.replace("iPhoneOS","")} ({crash_info["osVersion"]["build"]}){arch_type}/Symbols'

	arch_type = ''
	binary_images = crash_info['legacyInfo']['imageExtraInfo']
	dylib_path = ''
	for i in range(len(binary_images)):
		path = binary_images[i].get('path')
		if '/System/Library/Frameworks/' in path:
			dylib_path = path
			print(hex(crash_info['usedImages'][i][1]))
			break

	print(device_support_path+dylib_path)

def main():
	content = ''
	crash_info = {}
	crash_head_info = {}
	with open(crash_file, 'r') as f:
		lines = f.readlines()
		content = content + lines[0]
		crash_head_info = json.loads(lines[0])
		del lines[0]
		crash_info = "".join(lines)
		crash_info = json.loads(crash_info)

	content = content + 'Incident Identifier: ' + crash_info['incident'] + '\n'
	content = content + 'CrashReporter Key:   ' + crash_info['crashReporterKey'] + '\n'
	content = content + 'Hardware Model:      ' + crash_info['modelCode'] + '\n'
	content = content + 'Process:             ' + crash_info['procName'] + ' [' + str(crash_info['pid']) + ']' + '\n'
	content = content + 'Path:                ' + crash_info['procPath'] + '\n'
	content = content + 'Identifier:          ' + crash_info['bundleInfo']['CFBundleIdentifier'] + '\n'
	content = content + 'Version:             ' + crash_info['bundleInfo']['CFBundleVersion'] + ' (' + crash_info['bundleInfo']['CFBundleShortVersionString'] + ')' + '\n'
	content = content + 'Code Type:           ' + crash_info['cpuType'] + ' (Native)' + '\n'
	content = content + 'Role:                ' + crash_info['procRole'] + '\n'
	content = content + 'Parent Process:      ' + crash_info['parentProc'] + ' [' +  str(crash_info['parentPid']) + ']' + '\n'
	content = content + 'Coalition:           ' + crash_info['coalitionName'] + ' [' + str(crash_info['coalitionID']) + ']' + '\n'

	content = content + '\n'
	content = content + '\n'

	content = content + 'Date/Time:           ' + crash_info['captureTime'] + '\n'
	content = content + 'Launch Time:         ' + crash_info['procLaunch'] + '\n'
	content = content + 'OS Version:          ' + crash_info['osVersion']['train'] + ' (' + crash_info['osVersion']['build'] + ')' + '\n'
	content = content + 'Release Type:        ' + crash_info['osVersion']['releaseType'] + '\n'

	content = content + 'Baseband Version:    ' + crash_info['basebandVersion'] + '\n'
	content = content + 'Report Version:      104\n\n' # 取不到值

	content = content + 'Exception Type:  ' + crash_info['exception']['type'] + ' (' + crash_info['exception']['signal'] + ')' + '\n'
	exception_subtype = crash_info['exception'].get('subtype')
	if exception_subtype:
		content = content + 'Exception Subtype: ' + exception_subtype + '\n'

	exception_codes = crash_info['exception'].get('codes')
	if exception_codes:
		content = content + 'Exception Codes: ' + exception_codes + '\n'

	termination = crash_info.get('termination')
	if termination:
		termination_namespace = termination.get('namespace')
		termination_code = termination.get('code')
		if termination_namespace or termination_code:
			content = f'{content}Termination Reason: {termination_namespace}, Code {str(hex(termination_code))}\n'

		termination_description = termination.get('description')
		if termination_description:
			content = f'{content}Termination Description: {termination_description}\n'

	vmregioninfo = crash_info.get('vmregioninfo')
	if vmregioninfo:
		content = content + 'VM Region Info: ' + vmregioninfo + '\n'

	content = content + '\n'

	content = content + 'Triggered by Thread:  ' + str(crash_info.get('legacyInfo').get('threadTriggered').get('index')) + '\n'

	content = content + '\n'

	result = get_thread_content(crash_info)

	thread_content = result[0]
	max_address = result[1]
	
	content = content + thread_content

	thread_state_content = get_thread_state_content(crash_info)

	content = content + thread_state_content

	content = content + 'Binary Images:\n'

	content = content + get_binary_image_content(crash_info,crash_head_info,max_address)

	get_aslr_address(crash_info)

	with open(crash_file + '.txt' ,'w') as f:
		f.write(content)

main()

