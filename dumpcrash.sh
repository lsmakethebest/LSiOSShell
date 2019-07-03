#!/bin/bash
# echo $1
# echo $2
firstArch=$(dwarfdump --uuid "$1" | grep UUID | head -n 1)
secondArch=$(dwarfdump --uuid "$1" | grep UUID | tail -n 1)
# /Applications/Xcode.app/Contents/SharedFrameworks/DVTFoundation.framework/Versions/A/Resources
# 判断是否有值


echo "------------DSYM文件中信息--------------"
dsymProcess=${firstArch#*)}
dsymProcess=`basename $dsymProcess`
echo $dsymProcess
result1=${firstArch:5}
firstUUID=${result1%(*}
firstUUID=${firstUUID//"-"/""}
firstUUID=${firstUUID//" "/""}
firstUUID=`echo $firstUUID | tr '[A-Z]' '[a-z]'`

result2=${firstArch#*(}
firstArchName=${result2%)*}
echo "${firstArchName}:${firstUUID}"


result3=${secondArch:5}
secondUUID=${result3%(*}
secondUUID=${secondUUID//"-"/""}
secondUUID=${secondUUID//" "/""}
secondUUID=`echo $secondUUID | tr '[A-Z]' '[a-z]'`
result4=${secondArch#*(}
secondArchName=${result4%)*}
echo "${secondArchName}:${secondUUID}"

echo "------------crash文件中信息--------------"


process=$(grep Process "$2" | head -n 1)
process=${process%%[*} 
process=${process#*:} 
process=${process//" "/""}
if [[ $process == "" ]]; then
	process=$(grep Command "$2" | head -n 1)
	process=${process#*:} 
	process=${process//" "/""}
fi
echo $process



result=$(grep -n "Binary Images:" "$2")
result2=${result%%:*} #删除第一个:后面的字符串,保留左边
let "line=result2+1"
result=$(sed -n ${line}p "$2")


archResult=`grep Architecture "$2" | head -n 1`
if [[ $archResult != "" ]]; then
	arch=${archResult#*:}
	arch=${arch//" "/""}
else
	arch=${result%%<*}
	arch=${arch#*$process}
	arch=${arch//" "/""}
fi




uuid=${result%%>*} 
uuid=${uuid#*<} 
uuid=${uuid//"-"/""}
uuid=`echo $uuid | tr '[A-Z]' '[a-z]'`
echo ${arch}:$uuid
echo "-----------------------------------------"

dir=`dirname "$2"`
name=`basename "$2"`
newName=${dir}/${name}".txt"

#可通过以下命令查找symbolicatecrash所处位置
#find /Applications/Xcode.app -name symbolicatecrash -type f
cd /Applications/Xcode.app/Contents/SharedFrameworks/DVTFoundation.framework/Versions/A/Resources
if [[ $uuid == $firstUUID ]]; then
	./symbolicatecrash "$2" "$1" > $newName 0> /dev/null
	echo "--------------完成----------------"
	exit 1;
fi


if [[ $uuid == $secondUUID ]]; then
	./symbolicatecrash "$2" "$1" > "$newName" 0> /dev/null
	echo "--------------完成----------------"
	exit 1
fi

echo "crash文件和DSYM文件UUID不匹配"


