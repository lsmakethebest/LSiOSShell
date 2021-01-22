#!/usr/bin/python3
#coding:utf-8

import os
import sys
import json
import time
import datetime

def os_popen(cmd):
	return os.popen(cmd).read()

def is_folder(path):
	return os.path.isdir(path)

def get_file_mtime(path):
	if os.path.exists(path):
		update_time = os.path.getmtime(path)
		return update_time
	return ''

def get_file_info(path):
	if is_folder(path):
		path_list = sorted(os.listdir(path))
		result = []
		for i in path_list:
			if not i.startswith('.') and 'project.xcworkspace' not in i and 'xcuserdata' not in i:
				res = get_file_info(path + '/' + i)
				result.append(res)
		return {path:result}
	else:
		mtime = get_file_mtime(path)
		return {path:mtime}

def get_all_file_path(paths):
	result = []
	new_path = sorted(paths)
	for i in new_path:
		res = get_file_info(i)
		result.append(res)
	return result

def get_other_paths(path):
	result=os_popen(f'find -L {path} -iname "*.xcassets" -type d')
	new_result = []
	if result != '':
		result = result.split('\n')
		for i in result:
			if i != '':
				new_result.append(i)
	return new_result


def get_all_resources_path(path,pods_root,project_name):
	paths = []
	configuration = os.environ.get('CONFIGURATION')
	with open(path, 'r') as f:
		lines = f.readlines()
		find = False
		for i in range(len(lines)):
			line = lines[i].replace('\n','').strip().replace('install_resource ','').replace('${PODS_ROOT}',pods_root).replace('Pods/../','')
			str = 'CONFIGURATION" == "' + configuration
			if find and line != 'fi':
				line = line[1:-1]
				paths.append(line)
			if str in line:
				find = True

			if find and 'fi' == line:
				break
	start = datetime.datetime.now()
	other_paths = []
	current_path = os.getcwd()
	other_paths = other_paths + get_other_paths(f'{current_path}/{project_name}')
	other_paths = other_paths + get_other_paths(f'{current_path}/Pods')
	
	other_paths = sorted(other_paths)

	paths = paths + other_paths
	# print(f'获取other_paths耗时:${datetime.datetime.now() - start}')
	return paths

def get_resource_str(paths,last_file_path):
	result = get_all_file_path(paths)
	result_new_str = json.dumps(result)
	result_old_str = ""
	is_equal = False
	if os.path.exists(last_file_path):
		with open(last_file_path) as json_file:
			result_old_str = json_file.read()

	if result_new_str == result_old_str:
		is_equal =True

	if is_equal == False:
		if result_old_str == "":
			print(f'缓存文件不存在 {last_file_path}')
		else:
			print('新结果长度:' + str(len(result_new_str)))
			print('旧结果长度:' + str(len(result_old_str)))

			for i in range(len(result_new_str)):
				if result_new_str[i] == result_old_str[i]:
					continue
				print(f'\n不同下标:{str(i)}\n')
				length = 0
				diff_new_str = ''
				diff_old_str = ''
				for j in range(i,0,-1):
					diff_new_str = diff_new_str + result_new_str[j]
					diff_old_str = diff_old_str + result_old_str[j]
					length = length +1
					if length >100:
						break
				print('旧字符=>' + ''.join(reversed(diff_old_str)))
				print('新字符=>' + ''.join(reversed(diff_new_str)))
				break

	if is_equal:
		return [True,result_new_str]
	else:
		return [False,result_new_str]


def cache_resource():
	start = datetime.datetime.now()
	built_products_dir = os.environ.get('BUILT_PRODUCTS_DIR')
	last_file_path = built_products_dir + '/lastFile.txt'
	pods_root = os.environ.get('PODS_ROOT')
	project_name = os.environ.get('PROJECT_NAME')

	shell_path = pods_root + f'/Target Support Files/Pods-{project_name}/Pods-{project_name}-resources.sh'
	paths = get_all_resources_path(shell_path,pods_root,project_name)
	result = get_resource_str(paths,last_file_path)
	resource_equal = result[0]
	resource_str = result[1]

	add_resources = False
	if resource_equal:
		print('resources相同')
		print(f'resources最后编译缓存 => {last_file_path}')
	else:
		print('resources不相同')
		add_resources = True

	if add_resources:
		print('调用脚本')
		result = os_popen(shell_path.replace(' ','\ '))
		with open(last_file_path,'w') as f:
			print(f'将resources信息 写入 {last_file_path}\n')
			f.write(resource_str)

		print(result)
	else:
		print('不调用脚本')
	start_1 = datetime.datetime.now()

	unlocalized_resources_folder_path = os.environ.get('UNLOCALIZED_RESOURCES_FOLDER_PATH')
	rsync_result = os_popen(f'cp {built_products_dir}/tempAssets/Assets.car {built_products_dir}/{unlocalized_resources_folder_path}/Assets.car')
	if rsync_result:
		print(rsync_result)
	print(f'copy Assets.car耗时:{datetime.datetime.now()-start_1}')
	end = datetime.datetime.now()
	print(f'总共耗时:{end-start}')

def modify_xcodeproj(is_install):
	items = os.listdir(".")
	file_name = ''
	for name in items:
		if name.endswith(".xcodeproj"):
			file_name = name
			break
	if file_name == '':
		print('请到工程目录执行命令(如:/Users/liusong/Desktop/amap/iOS_5620)')
		return

	target_name = file_name.split('.')[0]
	pbxproj_path = f'{os.getcwd()}/{file_name}/project.pbxproj'
	content = ''
	content_new = ''
	with open(pbxproj_path,'r') as f:
		content = f.read()
		content_new = content

	config_sh_old = f'\\"${{PODS_ROOT}}/Target Support Files/Pods-{target_name}/Pods-{target_name}-resources.sh\\"\\n'
	config_sh_add = "/usr/local/bin/cresource add-resources\\n"

	config_sh_uninstall = config_sh_old
	config_sh_install = f'#{config_sh_old}{config_sh_add}'

	if is_install:
		if config_sh_add not in content:
			content_new = content.replace(config_sh_uninstall,config_sh_install)
	else:
		if config_sh_add in content:
			content_new = content.replace(config_sh_install,config_sh_uninstall)

	if content != content_new:
		with open(pbxproj_path,'w') as f:
			f.write(content_new)
			print('[CP] Copy Pods Resources 处理完成')
	else:
		print('[CP] Copy Pods Resources 无需处理')

	resources_sh_path = f'{os.getcwd()}/Pods/Target Support Files/Pods-{target_name}/Pods-{target_name}-resources.sh'

	sh_content = ''
	sh_content_new = ''
	with open(resources_sh_path,'r') as f:
		sh_content = f.read()
		sh_content_new = sh_content

	shell_content_old = 'rm -f "$RESOURCES_TO_COPY"'
	shell_content_add = 'UNLOCALIZED_RESOURCES_FOLDER_PATH="tempAssets"\nmkdir -p "${TARGET_BUILD_DIR}/${UNLOCALIZED_RESOURCES_FOLDER_PATH}"'

	shell_content_uninstall = shell_content_old
	shell_content_install = f'{shell_content_old}\n\n{shell_content_add}'

	if is_install:
		if shell_content_add not in sh_content:
			sh_content_new = sh_content.replace(shell_content_uninstall,shell_content_install)
	else:
		if shell_content_add in sh_content:
			sh_content_new = sh_content.replace(shell_content_install,shell_content_uninstall)

	if sh_content != sh_content_new:
		with open(resources_sh_path,'w') as f:
			f.write(sh_content_new)
			print(f'{os.path.basename(resources_sh_path)} 处理完成')
	else:
		print(f'{os.path.basename(resources_sh_path)} 无需处理')

def main():
	if len(sys.argv) > 1:
		if sys.argv[1] == 'add-resources':
			cache_resource()
		elif sys.argv[1] == 'install':
			modify_xcodeproj(True)
		elif sys.argv[1] == 'uninstall':
			modify_xcodeproj(False)
		else:
			print('请到工程目录执行 cresource install 或 cresource uninstall')
	else:
		print('请到工程目录执行 cresource install')

main()



