
#!/bin/bash
# @author liusong

RED='\033[31m'      # 红
GREEN='\033[32m'    # 绿
CYAN='\033[36m'     # 蓝
RES='\033[0m'         # 清除颜色

# 使用方式
# ./fetchDeviceSupport.sh 12,5 17D50

# 获取信息
# https://api.ipsw.me/v4/ipsw/iPhone12,5/17D50

need_verbose="0"
delete_ipsw_cache="1"

echoResult() {
	echo -e "${GREEN}${1}${RES}"
}

echoRed(){
	echo -e "${RED}${1}${RES}"
}

usage(){
	echoResult '请输入参数：'
	echoResult '\t必传参数1：Hardware Model'
	echoResult '\t必传参数2：OS Version 中的 buildId:例如：17D50'
	echoResult '\t可选参数 -d 处理完后，自动删除下载的ipsw文件，默认1，0：不删除 1：删除'
	echoResult '\t可选参数 -v 打印详细日志'
	echoResult '\t可选参数 -h 查看使用说明'
}


if [ $# -lt 2 ]; then
	usage
	exit
fi

cache_path="${HOME}/.ipswcache"
ipsw_path=$cache_path/ipsw
file_path=$ipsw_path/$1_$2.ipsw
output_path="$cache_path/unzip"
dyld_path="$cache_path/dyld"
hardware_model=$1
build_id=$2

shift 2
# 解析参数
while [ "$1" != "" ]; do
    case $1 in
        -d | --delete )
            shift
            delete_ipsw_cache="$1"
            ;;
        -v | --verbose )
            need_verbose="1"
            ;;
        -h | --help )
            usage
            ;;
        * )
            ;;
    esac

    # Next arg
    shift
done


function parse_json(){
    echo "${1//\"/}" | sed "s/.*$2:\([^,}]*\).*/\1/"
}

function get_url(){
	echo $1 | grep -Eo 'http:.*ipsw'
}

url="https://api.ipsw.me/v4/ipsw/"$hardware_model/$build_id
result=$(curl $url -s)
if [ "$result" =  "" ];then
	echo "未找到ipsw => "$url
	exit 0
fi


system_version=$(parse_json $result "version")
download_url=$(get_url $result)


# echo $result
# echo $system_version

if [ ! -d $cache_path ]; then
	mkdir $cache_path
fi

if [ ! -d $ipsw_path ]; then
	mkdir $ipsw_path
fi


echoResult "start downloading ipsw……"
echo $download_url"\n"

curl -C - -o $file_path $download_url

echoResult "download ipsw finish"
echoResult "start unzip ipsw……"

if [ ! -d $output_path ]; then
	mkdir -p $output_path
fi

if [ ! -d $dyld_path ]; then
	mkdir -p $dyld_path
fi

if [[ "$need_verbose" != "0" ]]; then
	unzip -o $file_path -d $output_path
else
	unzip -q -o $file_path -d $output_path
fi

echoResult "unzip ipsw finish"


cd $output_path
big_dmg=$(ls -S | head -1)

# 挂载地址
volume=$(hdiutil attach -noverify $big_dmg | tail -1 | awk '{print $3}' )
echo "dmg attach at: $volume"
dyldFolder=$volume"/System/Library/Caches/com.apple.dyld/*"

cp $dyldFolder $dyld_path

target_dyld_folder=$(find $dyld_path -name "dyld_shared*")
echo "dyld: "$target_dyld_folder

# 卸载
hdiutil detach $volume

# 删除无用 dyld_shared文件
rm -rf $output_path

archive_type=$(echo $target_dyld_folder | cut -d '_' -f 4)
tartget_folder="$system_version ($build_id) $archive_type"
cd -
device_support_path="${HOME}/Library/Developer/Xcode/iOS DeviceSupport/$tartget_folder/Symbols"
if [ ! -d "$device_support_path" ]; then
	mkdir -p "$device_support_path"
	# extract device support to someplace
	echoResult "start extract……"
	./dsc_extractor "$target_dyld_folder" "$device_support_path" "$need_verbose"
	echoResult "end extract……"
	echoResult "$device_support_path"
else
	echoRed "$device_support_path"
	echoRed "device support exists"
fi 

if [ -d $dyld_path ]; then
	rm -rf $dyld_path
fi


if [ "$delete_ipsw_cache" == "1" ]; then
	if [ -f $file_path ]; then
		rm -rf $file_path
	fi
fi


