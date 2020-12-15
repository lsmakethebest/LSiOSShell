#def xcodeproj_path(repo_clone_dir)
    # xcodeproj_file_paths = Dir["/Users/liusong/Desktop/DebugFramework/**/DebugFramework.xcodeproj"]
    #     xcodeproj_file_path = xcodeproj_file_paths[0]
    #     paths = xcodeproj_file_path.split("/")
    #     paths.delete_at(paths.length-1)
    #     xcodeproj_file_dir = paths.join("/")
    #     xcodeproj_file_dir = xcodeproj_file_dir + '/'
    #     xcodeproj_file_dir
    # puts xcodeproj_file_dir;
#end

#xcodeproj_path("/Users/liusong/Desktop/DebugFramework");

puts $*[0]


at_comp_dir_info = `dwarfdump --debug-info "#{$*[0]}" | head -500 | grep AT_comp_dir | head -1`
puts "at_comp_dir_info:#{at_comp_dir_info}"
if at_comp_dir_info.length==0
    puts "- #{framework_name} source map has removed,#{lib_path}"
    return nil
end
match_data = at_comp_dir_info.match(/.*AT_comp_dir(.*)\"(.*)\".*/)
if match_data.nil?
    puts "- #{framework_name} has no AT_comp_dir,#{lib_path}"
    return nil
end
puts "AT_comp_dir:#{match_data[2]}"

url = "https://github.com/lsmakethebest/LSSafeProtector"
# system("mkdir -p #{match_data[2]}")
system("git clone --depth 1 #{url} #{match_data[2]}")
match_data[2]
