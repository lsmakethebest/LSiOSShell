
### dsc_extractor 工具的编译
从苹果的开源网站(https://opensource.apple.com/tarballs/dyld/)里面下载dyld源码,这里下载的是最新的dyld-519.2.2.tar.gz版本。在高的一些dyld开源版本会提示找不到一些头文件，这个版本就可以提取。
解压下载的dyld压缩包，进入目录打开dyld-519.2.2/launch-cache/dsc_extractor.cpp 找到main函数
修改dsc_extractor.cpp文件，在653行，将#if预处理指令的条件判断0改为1。

终端进入到 dyld-519.2.2/launch-cache目录 编译dsc_extractor.cpp文件，执行下面命令
clang++ -o dsc_extractor ./dsc_extractor.cpp dsc_iterator.cpp

### 使用
- 打印过程
./dsc_extractor  target_dyld_folder" device_support_path 1
- 不打印过程
./dsc_extractor  target_dyld_folder" device_support_path 0

第三个参数不输入，默认为打印过程
