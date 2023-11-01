import os
#coding=utf8
import sys
import string
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import time
import datetime
import ssl
import numpy as np
import pandas as pd
import traceback
import csv
ssl._create_default_https_context = ssl._create_unverified_context
import json
import subprocess
import glob
import requests

def get_source_content(url):
    response = requests.get(url)

    if response.status_code == 200:
        return response.content
    else:
        return None
    
def get_sourcefiles(raw_url: str,) -> str:
    """
    Extract patch content from a GitHub raw URL and save it to a file.

    Parameters:
        raw_url (str): The raw URL of the GitHub patch file.
        output_file (str): The path to the output file where the patch content will be saved.

    Returns:
        str: The extracted raw content of the patch.
    """
    try:
        response = requests.get(raw_url)
        response.raise_for_status()
        print(response.status_code)

        # Extract the raw content
        raw_content = response.text

        return raw_content

    except requests.exceptions.RequestException as e:
        print("An error occurred while extrating", raw_url,e)

# find all the line numbers that the functions begins
def get_line_numbers(filename,lang_type):
    # found = False
    #cmd = "ctags -x --c-kinds=fp " + filename + " | grep " + funcname
    cmd = "ctags -x --"+lang_type+"-kinds=f " + filename

    output = subprocess.getoutput(cmd)
    lines = output.splitlines()
    line_nums = []
    for line in lines:
        line = line.split(" ")
        char = list(filter(None, line))
        line_num = char[2]
        line_nums.append(int(line_num))
    return line_nums

def process_file(filename, line_num):
    # print("opening " + filename + " on line " + str(line_num))

    code = ""
    cnt_braket = 0
    found_start = False
    found_end = False

    with open(filename, "r") as f:
        for i, line in enumerate(f):
            if(i >= (line_num - 1)):
                code += line

                if (not line.startswith("//")) and line.count("{") > 0:
                    found_start = True
                    cnt_braket += line.count("{")

                if (not line.startswith("//")) and line.count("}") > 0:
                    cnt_braket -= line.count("}")

                if cnt_braket == 0 and found_start == True:
                    found_end = True
                    return code, i+1
    
def get_diff_num(filename):
    diff_start_lines = []
    with open(filename, "r") as patch:
        for i, line in enumerate(patch):
            if line.startswith("@@ "):
                if not i == 0:
                    diff_start_lines.append(i)
        diff_start_lines.append(i+1)
    return diff_start_lines

def get_enumerate(filename):
    patch = open(filename, "r")
    return enumerate(patch)

def get_diff_information(filename, diff_start_lines):
    block_num = 0
    archor = []
    count = 0
    for diff_start_line in diff_start_lines:
        # reset some values
        count += 1
        minus_count = 0
        plus_count = 0
        before = None
        after = None
        start_line_num = None
        minus_pos = []
        plus_pos = []
        patch = []
        for j, l in get_enumerate(filename):
            if count == len(diff_start_lines):
                if j == diff_start_line - 1:
                    patch.append(l)
                    if l.startswith("-"):
                        minus_count += 1
                        minus_pos.append(j - start_line_num)
                    if l.startswith("+"):
                        plus_count += 1
                        plus_pos.append(j - start_line_num)
                    block_num = j
                    before = list(map(int, before))
                    after = list(map(int, after))
                    if len(archor) == 0:
                        archor.append(
                            [before, after, minus_count, plus_count, minus_pos, plus_pos, patch, after[0], minus_count,
                             0])
                    else:
                        diff_value = archor[-1][8] + minus_count
                        insert_after = after[0] + archor[-1][8]
                        last_end = archor[-1][1][0] + archor[-1][1][1] - 1
                        archor.append([before, after, minus_count, plus_count, minus_pos, plus_pos, patch, insert_after,
                                       diff_value, last_end])
                    break

                if block_num <= j < diff_start_line - 1:
                    patch.append(l)
                    if l.startswith("@@ "):
                        start_line_num = j
                        pos = l.find("@@ ")
                        end = l.find(" @@ ")
                        modified = l[pos + 3:end]
                        modified = modified.split(" ")
                        before = modified[0]
                        before = before.replace("-", "")
                        before = before.split(",")
                        after = modified[1]
                        after = after.replace("+", "")
                        after = after.split(",")
                        # now our source files are after-modified

                    if l.startswith("-"):
                        minus_count += 1
                        minus_pos.append(j - start_line_num)

                    if l.startswith("+"):
                        plus_count += 1
                        plus_pos.append(j - start_line_num)
                elif j < block_num:
                    continue
                else:
                    block_num = j
                    before = list(map(int, before))
                    after = list(map(int, after))
                    if len(archor) == 0:
                        archor.append(
                            [before, after, minus_count, plus_count, minus_pos, plus_pos, patch, after[0], minus_count,
                             0])
                    else:
                        diff_value = archor[-1][8] + minus_count
                        insert_after = after[0] + archor[-1][8]
                        last_end = archor[-1][1][0] + archor[-1][1][1] - 1
                        archor.append([before, after, minus_count, plus_count, minus_pos, plus_pos, patch, insert_after,
                                       diff_value, last_end])
                    break
            else:
                if block_num <= j < diff_start_line:
                    patch.append(l)
                    if l.startswith("@@ "):
                        start_line_num = j
                        pos = l.find("@@ ")
                        end = l.find(" @@ ")
                        modified = l[pos + 3:end]
                        modified = modified.split(" ")
                        before = modified[0]
                        before = before.replace("-", "")
                        before = before.split(",")
                        after = modified[1]
                        after = after.replace("+", "")
                        after = after.split(",")
                        # now our source files are after-modified

                    if l.startswith("-"):
                        minus_count += 1
                        minus_pos.append(j - start_line_num)

                    if l.startswith("+"):
                        plus_count += 1
                        plus_pos.append(j - start_line_num)
                elif j < block_num:
                    continue
                else:
                    block_num = j
                    before = list(map(int, before))
                    after = list(map(int, after))
                    if len(archor) == 0:
                        archor.append(
                            [before, after, minus_count, plus_count, minus_pos, plus_pos, patch, after[0], minus_count,
                             0])
                    else:
                        diff_value = archor[-1][8] + minus_count
                        insert_after = after[0] + archor[-1][8]
                        last_end = archor[-1][1][0] + archor[-1][1][1] - 1
                        archor.append([before, after, minus_count, plus_count, minus_pos, plus_pos, patch, insert_after,
                                       diff_value, last_end])
                    break

    return archor

def generate_line_diff(c_cpp_csv):
    vul_number = 0 
    lname=[]
    vul_functions_before = []
    vul_functions_after = []
    data=[]

    for index, row in c_cpp_csv.iterrows():
         try:   
            commit_id = row["commit_id"]
            # print("this is commit id",commit_id)
            diff = row["files_changed"]
            if not (row["cwe_id"] is None) and not (row["cwe_id"] == ""):
                CWE_ID = str(row["cwe_id"])
            else:
                CWE_ID = "others"
            files_changed = []
            project = row["project"]
            for i in diff.split("<_**next**_>"):
                files_changed.append(json.loads(i))

            # print("files_changed", files_changed)
            for file in files_changed:
                file_with_dir = file["filename"]
                # print("file_with_dir", file_with_dir)
                pos = file_with_dir.rfind('/')
                if pos > 0:
                    filename = file_with_dir[pos + 1:]
                    file_dir = commit_id + "/" + file_with_dir[:pos]
                elif pos == 0:
                    filename = file_with_dir[1:]
                    file_dir = commit_id
                else:
                    filename = file_with_dir
                    file_dir = commit_id
                raw_url=file["raw_url"]
                # print("raw_url",raw_url)
                if "patch" in file:
                    patch = file["patch"]
                else:
                    patch = ""
                type_pos = filename.find('.')
                if type_pos > 0:
                    only_name = filename[:type_pos]
                    # print("only_name", only_name)
                    only_type = filename[type_pos + 1:]
                    # print("only_type", only_type)

                else:
                    only_name = filename
                    only_type = "not know"
                
                sourcefiles = get_source_content(raw_url)
                if sourcefiles is not None:
                   sourcefiles_str = sourcefiles.decode('utf-8') 
                # print("sourcefiles",sourcefiles)
                # TODO: get sourcefiles from local
                if not os.path.exists("patchAll0206/" + only_type + '/' + project + '/' + CWE_ID + '/' + file_dir):
                    os.makedirs("patchAll0206/" + only_type + '/' + project + '/' + CWE_ID + '/' + file_dir)
                sourcefile_dir = "patchAll0206/" + only_type + '/' + project + '/' + CWE_ID + '/' + file_dir + '/' + filename
                # print("sourcefiledir",sourcefile_dir)
                patchfile_dir = "patchAll0206/" + only_type + '/' + project + '/' + CWE_ID + '/' + file_dir + '/' + only_name + '_' + 'patch.txt'
                # print(patchfile_dir,"<===>",sourcefile_dir)
                with open(sourcefile_dir, "w+") as source_file, open(patchfile_dir, "w+") as patch_file:
                    source_file.write(sourcefiles_str)
                    patch_file.write(patch)
                    # print("sourcefile_dir",sourcefile_dir)
                # get functions: if vul? not vul?
                if only_type == "c":
                    num = get_diff_num(patchfile_dir)
                    # print("num", num)
                    archors = get_diff_information(patchfile_dir, num)
                    # print("archors", archors)
                    block_num = 0
                    block_total = len(archors)
                    for archor in archors:
                        block_num += 1
                        # ************************************
                        # data=[]
                        del_line_pos = archor[4]
                        add_line_pos = archor[5]
                        patch_start = int(archor[1][0])
                        # print("patch_start", patch_start)
                        patch_lines = int(archor[0][1]) + archor[3]
                        # print("patch_lines", patch_lines)
                        patch_end = patch_start + patch_lines - 1
                        # print("patch_end", patch_end)
                        source_end = patch_start + int(archor[1][1]) - 1
                        # print("source_end", source_end)
                        last_end = archor[9]
                        # print("last_end", last_end)
                        wrote = False
                        add_patch_file_dir = "patchAll0206/" + only_type + '/' + project + '/' + CWE_ID + '/' + file_dir + '/' + "add_patch_" + filename
                        # print("add_patch_file_dir", add_patch_file_dir)
                        with open(sourcefile_dir, "r") as before, open(add_patch_file_dir, "a") as after:
                            lines = before.readlines()
                            # print("lines", lines)
                            flen = len(lines)
                            # print("flen", flen)
                            for i in range(flen):
                                if last_end - 1 < i <= source_end - 1:
                                    if i == 0:
                                        after.write(lines[i])
                                        continue
                                    if (patch_start - 1 <= i <= source_end - 1):
                                        if wrote == False:
                                            for patch_line in archor[6][1:]:
                                                # print("This is patch_line", patch_line,"************************************************************************************")
                                                # data.append(patch_line,commit_id)

                                                if patch_line.startswith("+"):
                                                    patch_line = patch_line.replace("+", "//fix_flaw_line_below:\n//",
                                                                                     1)
                                                    

                                                    # cwe20  hjhkkjb  ihkk
                                                    # cwe20  hjhkjkjkjkjb  ihkkjb
                                                if patch_line.startswith("-"):
                                                    patch_line = patch_line.replace("-", "//flaw_line_below:\n", 1)
                                                if not patch_line.endswith("\n"):
                                                    patch_line = patch_line + "\n"
                                                after.write(patch_line)
                                            wrote = True
                                    else:
                                        after.write(lines[i])
                                if block_num == block_total and source_end < flen and i > source_end - 1:
                                    after.write(lines[i])
                    line_nums = get_line_numbers(add_patch_file_dir, "c")
                    # print("line_nums", line_nums)
                    if len(line_nums) > 0:
                        for line_num in line_nums:
                            code, i = process_file(add_patch_file_dir, line_num)
                            if "//flaw_line_below:" in code or "//fix_flaw_line_below:\n//" in code:
                                print("This is code",code)
                                vul_number += 1
                                split_vul_dir = "./split0206/vul" + '/' + project + '/' + CWE_ID
                                if not os.path.exists(split_vul_dir):
                                    os.makedirs(split_vul_dir)
                                split_vul_file = split_vul_dir + '/' + CWE_ID + "_" + "add_patch_" + str(
                                    i) + "_" + filename
                                with open(split_vul_file, "w+") as vulFun:
                                    vulFun.write(code)
                                    
                                split_vul_dir_0 = "./split0206/vul0" + '/' + project
                                if not os.path.exists(split_vul_dir_0):
                                    os.makedirs(split_vul_dir_0)
                                split_vul_file_0 = split_vul_dir_0 + '/' + CWE_ID + "_""add_patch_" + str(
                                    i) + "_" + filename
                                with open(split_vul_file_0, "w+") as vulFun0:
                                    vulFun0.write(code)
                                cve_id = row["cve_id"]
                                cwe_id = row["cwe_id"]
                                project = row["project"]
                                commit_id = row["commit_id"]
                                result={
                                    "cve_id":cve_id,
                                    "cwe_id":cwe_id,
                                    "project":project,
                                    "commit_id":commit_id,
                                    "code":code,
                                    "line_num":i,
                                    "filename":filename,
                                    "type":only_type,
                                    "raw_url":raw_url
                                }
                                data.append(result)
                            else:
                                split_nonevul_dir = "./split0206/nonevul" + '/' + project
                                print("this is nonevul",code)
                                if not os.path.exists(split_nonevul_dir):
                                    os.makedirs(split_nonevul_dir)
                                split_nonevul_file = split_nonevul_dir + '/' + "add_patch_" + str(i) + "_" + filename
                                with open(split_nonevul_file, "w+") as nonVulFun:
                                    nonVulFun.write(code)
                        print("一共有 %d 个" % vul_number)
              
                elif only_type in ["C", "cc", "cxx", "cpp", "c++", "Cpp"]:
                    # print("\n\n\n cppcppcppcppcppcppcppcppcppcppcppcppcppcppcppcpp \n\n\n")
                    num = get_diff_num(patchfile_dir)
                    archors = get_diff_information(patchfile_dir, num)
                    block_num = 0
                    block_total = len(archors)
                    for archor in archors:
                        block_num += 1
                        del_line_pos = archor[4]
                        add_line_pos = archor[5]
                        patch_start = int(archor[1][0])
                        # 要在修改的地方加入多少行
                        patch_lines = int(archor[0][1]) + archor[3]
                        patch_end = patch_start + patch_lines - 1
                        source_end = patch_start + int(archor[1][1]) - 1
                        last_end = archor[9]
                        wrote = False
                        # 修改一次，就要加一次行差
                        add_patch_file_dir = "patchAll0206/" + only_type + '/' + project + '/' + CWE_ID + '/' + file_dir + '/' + "add_patch_" + filename
                        with open(sourcefile_dir, "r") as before, open(add_patch_file_dir, "a") as after:
                            lines = before.readlines()
                            flen = len(lines)
                            for i in range(flen):
                                if last_end - 1 < i <= source_end - 1:
                                    if i == 0:
                                        after.write(lines[i])
                                        continue
                                    if (patch_start - 1 <= i <= source_end - 1):
                                        if wrote == False:
                                            for patch_line in archor[6][1:]:
                                                if patch_line.startswith("+"):
                                                    patch_line = patch_line.replace("+", "//fix_flaw_line_below:\n//",
                                                                                    1)
                                                if patch_line.startswith("-"):
                                                    patch_line = patch_line.replace("-", "//flaw_line_below:\n", 1)
                                                if not patch_line.endswith("\n"):
                                                    patch_line = patch_line + "\n"
                                                after.write(patch_line)
                                            wrote = True
                                    else:
                                        after.write(lines[i])
                                if block_num == block_total and source_end < flen and i > source_end - 1:
                                    after.write(lines[i])
                    line_nums = get_line_numbers(add_patch_file_dir, "c++")
                    if len(line_nums) > 0:
                        for line_num in line_nums:
                            code, i = process_file(add_patch_file_dir, line_num)
                            if "//flaw_line_below:" in code or "//fix_flaw_line_below:\n//" in code:
                                vul_number += 1
                                split_vul_dir = "./split0206/vul" + '/' + project + '/' + CWE_ID
                                if not os.path.exists(split_vul_dir):
                                    os.makedirs(split_vul_dir)
                                split_vul_file = split_vul_dir + '/' + CWE_ID + "_" + "add_patch_" + str(
                                    i) + "_" + filename
                                with open(split_vul_file, "w+") as vulFun:
                                    vulFun.write(code)
                                split_vul_dir_0 = "./split0206/vul0" + '/' + project
                                if not os.path.exists(split_vul_dir_0):
                                    os.makedirs(split_vul_dir_0)
                                split_vul_file_0 = split_vul_dir_0 + '/' + CWE_ID + "_""add_patch_" + str(
                                    i) + "_" + filename
                                with open(split_vul_file_0, "w+") as vulFun0:
                                    vulFun0.write(code)
                            else:
                                split_nonevul_dir = "./split0206/nonevul" + '/' + project
                                if not os.path.exists(split_nonevul_dir):
                                    os.makedirs(split_nonevul_dir)
                                split_nonevul_file = split_nonevul_dir + '/' + "add_patch_" + str(i) + "_" + filename
                                with open(split_nonevul_file, "w+") as nonVulFun:
                                    nonVulFun.write(code)
                        print("一共有 %d 个" % vul_number)

         except Exception as e:
            traceback.print_exc(file=sys.stdout)
            print("reason", e)
            print("\n commit_id:" + str(commit_id) + "！")
            print("\n index:" + str(index) + "！")
            continue

    print(data)
if __name__ == '__main__':
    c_cpp_csv = pd.read_csv('all_c_cpp_release2.0.csv',nrows=10, encoding='utf-8')
    result=generate_line_diff(c_cpp_csv)