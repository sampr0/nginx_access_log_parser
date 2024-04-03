#!/usr/bin/env python
# encoding: utf-8
# Author: s1mpr0
import re
import argparse
import openpyxl
import io
import datetime
import urllib.parse

def find(pat,text):
    format_info = {}
    match = re.match(pat, text)
    if match:
        return match.groupdict()
    else:
        return {}
def extend_info(format_info):
    #扩展后缀信息
    format_info['file_name_suffix'] = ''
    format_info['referer_host'] = ''
    if format_info.get('uri'):
        urllib.parse.urlparse(format_info.get('uri'))
        if '/' in urllib.parse.urlparse(format_info.get('uri')).path:
            file_name = urllib.parse.urlparse(format_info.get('uri')).path.split('/')[-1]
            if '.' in file_name:
                file_name_suffix = file_name.split('.')[-1]
                if file_name_suffix:
                    format_info['file_name_suffix'] = file_name_suffix
    if format_info.get('referrer'):
        tmp_host =  urllib.parse.urlparse(format_info.get('referrer')).hostname   
        if tmp_host:
            format_info['referer_host'] = tmp_host
    if format_info.get('datetime'):
        

        # 转换前的格式
        original_format = "%d/%b/%Y:%H:%M:%S %z"

        # 转换为datetime对象
        datetime_obj = datetime.datetime.strptime(format_info.get('datetime'), original_format)

        # 设定目标格式
        target_format = "%Y/%m/%d %H:%M:%S"
        # 转换为目标格式的字符串
        converted_datetime_str = datetime_obj.strftime(target_format)
        format_info['datetime'] = converted_datetime_str

def parse_line_log(log_line):
    format_infos = []
    #print(log_line)
    pats = [
            r'(?P<ip>\d+\.\d+\.\d+\.\d+) - (?P<username>\S+) \[(?P<datetime>.+?)\] "(?P<method>\w+) (?P<uri>.+?) HTTP/1.1" (?P<status>\d+) (?P<length>\d+) "(?P<referrer>.+?)" "(?P<user_agent>.+?)"',
            r'(?P<ip>\d+\.\d+\.\d+\.\d+) - (?P<username>\S+) \[(?P<datetime>.+?)\] "(?P<method>\w+) (?P<uri>.+?)" (?P<status>\d+) (?P<length>\d+) "(?P<referrer>.+?)" "(?P<user_agent>.+?)"',
            r'(?P<ip>\d+\.\d+\.\d+\.\d+) - (?P<username>\S+) \[(?P<datetime>.+?)\] "(?P<uri>.+?)" (?P<status>\d+) (?P<length>\d+) "(?P<referrer>.+?)" "(?P<user_agent>.+?)"',
            r'(?P<ip>\d+\.\d+\.\d+\.\d+) - (?P<username>\S+) \[(?P<datetime>.+?)\] "" (?P<status>\d+) (?P<length>\d+) "(?P<referrer>.+?)" "(?P<user_agent>.+?)"',
        ]
    #if '/cgi-bin/readycloud_control.cgi' in log_line:
    #    import pdb;pdb.set_trace()
    for pat in pats:
        format_info = find(pat, log_line)
        if format_info:
            extend_format_info = extend_info(format_info)
            format_infos.append(format_info)
            break
    return format_infos
def reorder_keys(keys):
    new_keys = []
    keys = [k for k  in keys]
    first_seqs = ['ip','username','datetime','file','status','method','uri','file_name_suffix','referer_host','referrer','user_agent']
    for _seq in first_seqs:
        if _seq in keys:
            new_keys.append(_seq)
            keys.remove(_seq)
    if keys:
        for _key in keys:
            new_keys.append(_key)
    return new_keys
def transkeys2chinese(keys):
    chinese_keys = {
        'file_name_suffix':'文件后缀',
        'datetime':'时间',
    }
    return [chinese_keys.get(key,key) for key in keys]
    


def trans2excel(log_infos:list):
    print('writing to excel')
    wrorkbook = openpyxl.Workbook()
    sheet = wrorkbook.active
    if log_infos:
        keys_seq = reorder_keys(log_infos[0].keys())
        sheet.append(transkeys2chinese(keys_seq))
        for log_info in log_infos:
            sheet.append([log_info.get(key,'') for key in keys_seq ])
    file_name = 'accesslog_{}.xlsx'.format(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')).replace(' ','_'))
    wrorkbook.save(filename = file_name)
    print('The log file has been parsed and saved as {}'.format(file_name))

def process(file_name:str):
    if not file_name:
        return False
    lines = open(file_name,'r').readlines()
    line_count = len(lines)
    log_infos = []
    error_line_count = 0
    i = 1
    for line in lines:
        tmp_infos = parse_line_log(line)

        if tmp_infos and isinstance(tmp_infos, list):
            log_infos.append(tmp_infos[0])
        else:
            error_line_count = error_line_count + 1
            print('Error line:{}'.format(line))
        if i % 1000 == 0:
            print('Processing {}/{} = {}%,with error line count:{}'.format(i,line_count,int(i * 100 / line_count),error_line_count))
        i = i + 1
    if log_infos:
        trans2excel(log_infos)
        
        
#从命令行传入文件名


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Parse log file,usage: parselog.py -f filename')
    parser.add_argument('-f','--file_name',type=str,help = 'please input the log file path and name')
    args = parser.parse_args()
    process(args.file_name)