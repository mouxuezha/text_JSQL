import xlrd 
import datetime
import os
import sys
import random
import numpy as np
import json
# import resource # caole 这个只在unix的里面有，win的里面没有
# import psutil # 算了，考虑到内网更新库的蛋疼性，不引入其他包了凑活用把

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

def load_bridge_json(json_file):
    # 这个是用来从桥梁的json文件里面读取出坐标的，暂时只要坐标就行了。
    with open(json_file, 'r', encoding='utf-8') as wenjian:
        json_data = json.load(wenjian)

    # 先夹杂JSON文件

    bridge_list = [] 

    # 然后循环一波
    for i in range(len(json_data)):
        field_single = json_data[i]
        for Neighbor in field_single["Neighbor"]:
            try:
                BridgeState_single = Neighbor["BrigeState"] # 这里JSON里有拼写错误，将错就错了。
                for j in range(len(BridgeState_single)): 
                    try:
                        bridge_LLA_single =  [BridgeState_single[j]["start_lon"], BridgeState_single[j]["start_lat"],0]
                        bridge_list.append(bridge_LLA_single)
                    except:
                        pass
            except:
                pass
            
    return bridge_list

# def check_memory():
#     # 这个是用于辅助调试的，检测内存占用，如果超过了一定程度就杀线程。
#     # memory_usage =resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024*1024)
#     memory_usage = psutil.virtual_memory()
#     memory_usage = memory_usage.used / (1024*1024)
#     print(memory_usage)

if __name__ == "__main__":
    flag = 1
    if flag==0:
        json_file = "beifen\\Bridge.json"
        jieguo = load_bridge_json(json_file)
    elif flag ==1:
        # check_memory()
        pass 