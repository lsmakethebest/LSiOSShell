#!/usr/bin/python3
# coding: utf-8

import sys, getopt, re, os

AMapiPhone_end_adrr_fixup = "0"
def fixup(inputfile, outputfile):
  global AMapiPhone_end_adrr_fixup
  # print ('输入的文件为：', inputfile)
  # print ('输出的文件为：', outputfile)
    # 1. 读取文件
  f = open(inputfile, 'r')
  content = f.read()
  # Binary Images:
  # 0x1028c0000 - 0x102ac7fff AMapiPhone arm64

  # 2. 查找其实位置
  searchObj = re.search('(.*) - (.*) AMapiPhone', content)
  AMapiPhone_start_adrr = searchObj.group(1)
  AMapiPhone_end_adrr = AMapiPhone_end_adrr_fixup = searchObj.group(2)
  # print("start: " + AMapiPhone_start_adrr + " end: " + AMapiPhone_end_adrr)
  f.close()

  # 3. fixup
  def fixup(line):
    global AMapiPhone_end_adrr_fixup
    searchO = re.search(r'(.*)(\?\?\?)(.*) (.*)(0 \+)(.*)', line)
    sidle = int(searchO.group(3), 16) - int(AMapiPhone_start_adrr, 16)
    line_fixup = searchO.group(1) + searchO.group(2) + searchO.group(3) + " " + AMapiPhone_start_adrr  + " + " + str(sidle)
    line_fixup = line_fixup.replace("???       ", "AMapiPhone")
    
    binary_end_fixup_offset = int(searchO.group(3), 16) - int(AMapiPhone_end_adrr_fixup, 16)
    
    if binary_end_fixup_offset > 0 :
      AMapiPhone_end_adrr_fixup = searchO.group(3).strip()
    return line_fixup

  # 4   ???                               0x000000010676828c 0 + 4403397260
  content_fixup = ""
  f = open(inputfile, 'r')
  for line in f.readlines():
    line = line.strip()
    if line.find("???") > 0:
      content_fixup += fixup(line)
    else:
      content_fixup += line
    content_fixup += "\n"
    
  # 5 fixup AMapiPhone endress
  origin = str(AMapiPhone_start_adrr) + " - " + str(AMapiPhone_end_adrr) + " AMapiPhone"
  origin_fixup = str(AMapiPhone_start_adrr) + " - " + str(AMapiPhone_end_adrr_fixup) + " AMapiPhone"
  content_fixup = content_fixup.replace(origin, origin_fixup)
  
  
  fwrite = open(outputfile, "w")
  fwrite.write(content_fixup)
  fwrite.close()

def main(argv):
  inputfile = ''
  outputfile = ''
  try:
    opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
  except getopt.GetoptError:
    print ('python3 fixup.py -i <inputfile> ')
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-h':
        print ('python3 fixup.py -i <inputfile>')
        sys.exit()
    elif opt in ("-i", "--ifile"):
        inputfile = arg
    elif opt in ("-o", "--ofile"):
        outputfile = arg
  if len(outputfile) == 0:
    basename = os.path.basename(inputfile)
    out_basename = basename.split(".")[0] + "_fixup." + basename.split(".")[1]
    outputfile = inputfile.replace(basename, out_basename)
  fixup(inputfile, outputfile)


if __name__ == "__main__":
   main(sys.argv[1:])








