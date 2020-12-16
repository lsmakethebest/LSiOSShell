#!/usr/bin/env python3
#coding:utf-8

import os
import sys
import json
import time
import requests

native_base_bundles_path = '/SCM/Local/TitanBaseline/NativeBaseBundles.json'
local_source_bundles_path = '/SCM/Local/LocalSourceBundlesConfig.json'
cache_path = '/Users/ios/.jenkins/workspace'
bundle_info_url = ''

def os_popen(cmd):
    # 执行 os.system(cmd)，返回执行结果
    return os.popen(cmd).read().replace('\n','')

# 加载本地json文件，返回为对象
def load_json(path):
    if not os.path.exists(path):
        print(f'load json 失败：{path} 不存在')
    with open(path) as f:
        return json.load(f)

def get_local_framework_path(bundle):
	# /Users/liusong/Desktop/amap/iOS_5176_1/Pods/RouteCommute/RouteCommute.framework
	return os.getcwd() + '/Pods/' + bundle + '/' + bundle + '.framework/' + bundle

# 根据二进制获取编译时的目录，拉取源码时需要放到此目录
def get_bundle_comp_dir(framework_path):
	# DW_AT_comp_dir	("/Users/liusong/TestSDK")
	# 先head 500行是为了加快处理速度，如果直接grep在head 1 会比较慢
	target_dir = os_popen(f'dwarfdump "{framework_path}" | head -500 | grep AT_comp_dir | head -1 | cut -d \\" -f 2')
	return target_dir


# 获取本地bundle的framework对应的commit和url
def get_bundle_url_and_commitid(bundle_name,baseline_bundles):
	data = {}
	for bun in baseline_bundles:
		if bun['artifactId'] == bundle_name:
			result = get_bundle_url('com.amap.ios.bundle',bun['artifactId'],bun['version'])
			if result['code'] != 1:
				print('获取失败')
				exit()
			else:
				data = result['data']
			break
	return data

# 获取指定bundle.framework的信息
def get_bundle_url(group_id,artifact_id,version):
	url = bundle_info_url + group_id + ":" + artifact_id + ":" + version + "/"
	resp = requests.get(url)
	jsonRelut = json.loads(resp.text)
	return jsonRelut


# 获取本地iOS bundle 基线信息
def get_all_baseline_bundles_info():
	path = os.getcwd() + native_base_bundles_path;
	data = load_json(path)
	return data

# 获取当前目录下xcworkspace目录
def get_workspacePath():
	items = os.listdir(".")
	newlist = []
	for names in items:
		if names.endswith(".xcworkspace"):
			newlist.append(names)
	if len(newlist) > 0:
		return os.getcwd() + '/' + newlist[0]
	else:
		print('目录不对，未获取到 xcworkspace 文件')
		exit()

# 拉取源码到指定目录，并切换为指定commit
def batch_pull_bundle(url,sourcePath,branch,commit_id):
	current_path = os.getcwd()
	if not os.path.exists(sourcePath):
		print('仓库不存在')
		if not os.path.exists(cache_path):
			os.system(f'sudo mkdir -p {cache_path}')
			# 第一次clone需授予权限
			os.system(f'sudo chmod -R 777 {cache_path}')
		os.system(f'git clone -b {branch} --single-branch {url} {sourcePath}')
		os.chdir(sourcePath)
		os.system(f'git reset {commit_id} --hard')
		os.chdir(current_path)
	else:
		print('仓库存在 执行更新')
		os.chdir(sourcePath)
		  # 判断是否有需要 stash 的文件: git diff HEAD
		need_stash = not os_popen('git diff HEAD').strip() == ''
		if need_stash:
			os.system('git stash')
		os.system('git fetch --all --prune')
		os.system(f'git checkout {branch} && git pull')
		os.system(f'git reset {commit_id} --hard')
		if need_stash:
			os.system('git stash pop')
		os.chdir(current_path)

# 将源码添加到工程中
def addXcodeproj(workspace_path,xcodeproj_path,bundleName):
	# 插入到主工程前面，为了区分哪些是debug bundle，主工程下面的是开发bundle
	with open(workspace_path + '/contents.xcworkspacedata', 'r') as f:
		lines = f.readlines()
		index = -1
		for i in range(len(lines)):
			if bundleName in lines[i]:
				index = i
				break
		if index > 0:
			del lines[i-1:i+2]

		lines.insert(len(lines)-1,f'   <FileRef\n      location = \"group:{xcodeproj_path}\">\n   </FileRef>\n')
		s = ''.join(lines)  # 将列表转换为string
	with open(workspace_path + '/contents.xcworkspacedata', 'w') as f:     # 写文件，开始的时候会先清空原文件，参考w的用法。如果不用with open，只是open，要注意最后将文件关闭。
		f.write(s)

#添加到workspace中会编译报错，所以需要想办法不让工程触发源码编译
def change_bundle_pbxproj(path,bundle):
	path = path + '/project.pbxproj'
	content = ''
	with open(path, 'r') as f:
		content = f.read()
		content = content.replace('WRAPPER_EXTENSION = framework','WRAPPER_EXTENSION = tempxxxx')
		
	with open(path, 'w') as f:
		f.write(content)



# 将bundle切换为源码仅用于调试不会用此代码编译
def checkout_all_bundle(baseline_bundles,debug_bundles,all_not_source_bundles):
	workspace_path = get_workspacePath()
	for bundle_name in debug_bundles:
		if bundle_name not in all_not_source_bundles:
			print(f'error:【{bundle_name}】 bundle名字不正确，或者此bundle已经被cab为源码了')
			exit()
		data = get_bundle_url_and_commitid(bundle_name,baseline_bundles)
		framework_path = get_local_framework_path(bundle_name)
		sourceCodePath = get_bundle_comp_dir(framework_path)
		repo = data['repo']
		if '/var/imkit' not in sourceCodePath:
			#.m文件目录和AT_comp_dir目录不一致，所以需要重新修改
			sourceCodePath = sourceCodePath.replace('Pods','DevPods')
			index = repo.find('amap_bundle')
			sourceCodePath = sourceCodePath + '/' + repo[index:-4]
		print(f'pulling => {repo}  \nbranch:{data["branch"]} \ncommitId:{data["commitId"]} \npath:{sourceCodePath}')
		batch_pull_bundle(data['repo'], sourceCodePath,data['branch'],data['commitId'])
		print('adding ' + bundle_name + ' to xcworkspace')
		xcodeproj_path = sourceCodePath + "/" + bundle_name + '.xcodeproj'
		change_bundle_pbxproj(xcodeproj_path,bundle_name)
		addXcodeproj(workspace_path,xcodeproj_path,bundle_name)
		print('----------------------------------------------------')

def clear_all_cache():
	os_popen(f'sudo rm -rf {cache_path}')

def delete_bundles(bundles):
	add_bundles = []
	add_bundles_info = {}
	workspace_path = get_workspacePath()
	lines = None
	with open(workspace_path + '/contents.xcworkspacedata', 'r') as f:
		lines = f.readlines()
		for i in range(len(lines)):
			line = lines[i]
			if "group:/Users/ios/.jenkins/workspace" in line or "group:/var/imkit/" in line:
				bundle_name = os.path.basename(line).replace('.xcodeproj">','').replace('\n','')
				add_bundles.append(bundle_name)
				add_bundles_info[bundle_name] = line
	if bundles == None:
		bundles = add_bundles

	for bundle_name in bundles:
		if bundle_name not in add_bundles:
			print(f'error:【{bundle_name}】名字错误或者没有被添加到工程中，所以不能移除，请检查确认')
			exit()
		line = add_bundles_info[bundle_name]
		index = lines.index(line)
		del lines[index-1:index+2]
		# location = "group:/Users/ios/.jenkins/workspace/com.amap.ios.bundle_AMapNetwork_1.0.0.20201201231437/iOS_5785/DevPods/amap_bundle_amapnetwork/AMapNetwork.xcodeproj">
		# location = "group:/var/imkit/0bbf9a8f41cce10398f1450969f8e3c2/amap_bundle_lib_fmdb/FMDB.xcodeproj">
		path = ''
		result = line.split('/')
		if 'var/imkit/' in line:
			path = '/' + result[1] + '/' + result[2] + '/' + result[3]
		else:
			path = '/' + result[1] + '/' + result[2] + '/' + result[3] + '/' + result[4] + '/' + result[5]
		print(path)
		os_popen(f'rm -rf {path}')

	s = ''.join(lines)  # 将列表转换为string
	with open(workspace_path + '/contents.xcworkspacedata', 'w') as f:     # 写文件，开始的时候会先清空原文件，参考w的用法。如果不用with open，只是open，要注意最后将文件关闭。
		f.write(s)


# 获取本地已经切为源码的bundles
def get_source_code_bundles():
	result = load_json(os.getcwd() + local_source_bundles_path)['bundles']
	bundles = []
	for bundle_info in result:
		bundles.append(bundle_info['artifactId'])
	return bundles


def get_all_framework_bundles():
	bundles = get_all_baseline_bundles_info()
	bundle_names = []
	for bundle in bundles:
		bundle_names.append(bundle['artifactId'])
	return bundle_names

def get_all_not_source_bundles():
	all_bundles = get_all_framework_bundles()
	source_bundles = get_source_code_bundles()
	for bundle_name in source_bundles:
		if bundle_name in all_bundles:
			all_bundles.remove(bundle_name)
	return all_bundles

def main():
	if len(sys.argv) < 2:
		print('二进制调试\n  \tcd 工作目录(AMapiPhone.xcworkspace所在目录)\n \t ldebug add RouteCommute,MainBundle\n添加所有非源码bundle\n\tldebug add')
		print('\n从项目中删除project以及拉取的源码\n \tcd 工作目录(AMapiPhone.xcworkspace所在目录)\n\tldebug delete RouteCommute,MainBundle\n删除所有\n\tldebug delete')
		print('\n删除代码缓存(拉取的二进制源码)\n \tldebug clear')
		exit()

	starttime = time.time()

	is_all = None
	bundles = []
	all_not_source_bundles = get_all_not_source_bundles()
	if len(sys.argv) == 3:
		is_all = False
		bundles = sys.argv[2].split(',')
	else:
		is_all = True
		bundles = all_not_source_bundles
	bundles.sort()

	

	if sys.argv[1] == 'del' or sys.argv[1] == 'delete':
		delete_bundles(bundles if is_all == False else None)
	elif sys.argv[1] == 'add':	
		baseline_bundles = get_all_baseline_bundles_info()
		checkout_all_bundle(baseline_bundles,bundles,all_not_source_bundles)
	elif sys.argv[1] == 'clear':
		clear_all_cache()

	endtime = time.time()
	print(f'耗时：{endtime - starttime}')

main()





