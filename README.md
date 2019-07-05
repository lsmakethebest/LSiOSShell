# LSiOSShell
iOS shell相关脚本
### build_framework.sh 打包framework或.a静态库。并合成真机和模拟器
sh build_framework.sh xcodeproj目录 Debug/Release
```
  //参数二不传默认Release
  sh build_framework.sh /Users/liusong/Documents/TestFramework Debug
```
如果主工程不是静态库或动态库，可以 sh build_framework.sh  xcodeproj目录 Debug/Release  静态库或动态库target名称
```
  //指定targetName情况 必须指定是Debug或Release 不可省略此参数
  sh build_framework.sh /Users/liusong/Documents/TestFramework Debug  FrameworkA
```

### dumpcarsh.sh 解析.crash文件 利用系统自带的symbolicatecrash
sh dumpcarsh.sh dsym文件   crash文件 (解析后生成一个.txt文件在.crash同目录)
```
sh dumpcrash.sh /Users/liusong/Downloads/xxxx.dSYM /Users/liusong/Desktop/xxxxx2019-7-1,6-18PM.crash
```
