import xlrd 
import datetime
import os
import sys
import random
import numpy as np
import shutil

def get_states(env):
    result = env.GetCurrentStatus()
    while (env.statusparser(result) == None):
        env.Step()
        result = env.GetCurrentStatus()
    redState, blueState = env.statusparser(result)
    return redState, blueState

def auto_save_file_name(log_folder = r'C:\Users\42418\Desktop\2024ldjs\EnglishMulu\auto_test'):
    # xxh 0909 for auto test
    log_file = log_folder + r'\auto_test_log' + str(0) + r'.txt'
    for i in range(114514): # 生成一个不会重复的文件名
        if os.path.exists(log_file):
            log_file = log_folder + r'\auto_test_log' + str(i+1) + r'.txt'
        else:
            break
    return log_file

def auto_save_check_index(log_folder = r'C:\Users\42418\Desktop\2024ldjs\EnglishMulu\auto_test'):
    # xxh 0912 for auto test
    log_file = log_folder + r'\auto_test_log' + str(0) + r'.txt'
    for i in range(114514): # 生成一个不会重复的文件名
        if os.path.exists(log_file):
            log_file = log_folder + r'\auto_test_log' + str(i + 1) + r'.txt'
        else:
            log_file_index = i
            break
    return log_file_index

def auto_save(log_file, tips, cur_redState, cur_blueState):
    # xxh 0909 for auto test
    file = open(log_file, 'a')
    file.write('this is ' + str(datetime.datetime.now()) + tips + '\n\n')
    file.write(cur_redState + '\n')
    file.write(cur_blueState)
    file.write('\n\n\n')
    file.close()
    return 0

def auto_state_filter(state_dic):
    if len(state_dic) == 0:
        strbuffer = "debug, no state"
        dic_key_list = [] 
        return strbuffer, dic_key_list 
    # for auto_test
    strbuffer = 'state recorded: '
    dic_key_list = list(state_dic.keys())
    geshu = len(dic_key_list)
    for i in range(geshu):
        strbuffer = strbuffer + '\n' + dic_key_list[i]
    strbuffer = strbuffer + '\n unit number: ' + str(geshu)
    return strbuffer, dic_key_list

def auto_state_compare(cur_State_list, start_State_list):
    strbuffer = "\n 目前已经摧毁的装备："
    for start_State in start_State_list:
        if start_State in cur_State_list:
            pass
        else:
            strbuffer = strbuffer + "\n " + start_State

    return strbuffer

def auto_state_compare2(cur_State_list, next_State_list):
    # 如果这一步有毁伤，那就返回这一步毁伤了什么，如果这一步没有毁伤，自然就不返回了。
    # 到时候另开一个，只记录这个，岂不美哉。
    strbuffer = ""
    jishu = 0
    for cur_unit in cur_State_list:
        if cur_unit in next_State_list:
            pass
        else:
            strbuffer = strbuffer + " " + cur_unit
            jishu = jishu + 1

    return strbuffer, jishu

def auto_target_estimage(target_unit_type,modify_index):
    if (target_unit_type == "Infantry"):
        modify_index = modify_index + 8
    if (target_unit_type == "missile_truck"):
        modify_index = modify_index + 8
    if (target_unit_type == "Infantry") or (target_unit_type == "missile_truck"):
        ID_target = target_unit_type + str(modify_index)
    else:
        ID_target = target_unit_type + '_' + str(modify_index)
    return ID_target

def auto_save_overall(str_buffer, log_file = r'C:\Users\42418\Desktop\2024ldjs\EnglishMulu\auto_test\overall_result.txt'):
    file = open(log_file, 'a')
    file.write(str_buffer + '\n')
    file.close()
    return 0

def load_agents(sorce_location, player="red"):
    # 先全都复制过来，复制过里啊之后再把.git删了，就算是完成了一次更新。
    # 先获取以下当前路径。
    if player=="red":
        # target_location = r"D:\EnglishMulu\text_JSQL\agent_guize\me_AI"
        target_location = sys.path[0] + r"\me_AI"
    elif player=="blue":
        # target_location = r"D:\EnglishMulu\text_JSQL\agent_guize\enemy_AI"
        target_location = sys.path[0] + r"\enemy_AI"
    
    # 先把之前的删了。
    shutil.rmtree(target_location)

    # 然后一整个文件夹复制过去
    shutil.copytree(sorce_location, target_location)

    # 然后把里面的.git文件夹删了。
    git_location = target_location + r"\.git"
    # shutil.rmtree(git_location) # 算了，这个会爆权限问题，手动删一下也就罢了。
    
    pass

if __name__ == "__main__":
    # 在这里实现一个装载智能体的功能，然后重新整理一下那些调用关系。
    # 文件系统的结构也得重新琢磨一下了，比较理想的是enemy_AI和me_AI这层让它对应好了。
    red_location = r"D:\EnglishMulu\AI_test_2024"
    blue_location = r"D:\EnglishMulu\AI_test_2024"
    load_agents(red_location, player="red")
    load_agents(blue_location, player="blue")