#coding:utf-8
"""
下载分钟线数据脚本
用于下载股票的历史分钟线数据，支持增量下载
"""

import json
from xtquant import xtdata
import pandas as pd
from datetime import datetime, timedelta
import os
import glob
xtdata.enable_hello = False

# 获取当前时间
current_time = datetime.now().strftime('%H:%M')
today_str = datetime.now().strftime('%Y%m%d')

# 检查本地最新分钟线数据时间
try:
    # 检查某只股票的分钟线数据，判断最新数据时间
    local_data = xtdata.get_local_data(
        field_list=['open',],
        stock_list=['600795.SH'],
        count=2,
        period='1m'  # 分钟线
    )['600795.SH']
    
    if len(local_data) == 0:
        new_data_time = ''
        print('本地没有分钟线数据')
    else:
        # 获取最新数据的时间
        last_time = local_data.index[-1]
        if isinstance(last_time, pd.Timestamp):
            new_data_time = last_time.strftime('%Y%m%d')
            new_data_datetime = last_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            new_data_time = pd.Timestamp(last_time).strftime('%Y%m%d')
            new_data_datetime = pd.Timestamp(last_time).strftime('%Y-%m-%d %H:%M:%S')
        print(f'本地最新分钟线数据时间: {new_data_datetime}')
except Exception as e:
    print(f'检查本地分钟线数据时出错: {e}')
    new_data_time = ''
    new_data_datetime = ''

# 下载板块数据（如果需要）
sector_list = xtdata.get_sector_list()
if not sector_list:
    xtdata.download_sector_data()

#___________________________________________________________
# 获取股票列表
# 可以根据需要修改股票池，例如：
# 1. 使用全部A股：stock_list = xtdata.get_stock_list_in_sector('沪深A股')
# 2. 使用自定义股票池：从文件读取
# 3. 使用特定板块：stock_list = xtdata.get_stock_list_in_sector('板块名称')

# 方法1：使用全部A股（数据量大，下载时间长）
stock_list = xtdata.get_stock_list_in_sector('沪深A股')

# 方法2：从股票池文件读取（推荐，可以只下载需要的股票）
# file_path = './配置文件/股票池.txt'
# try:
#     with open(file_path, 'r', encoding='utf-8') as file:
#         stock_list = [line.strip() for line in file.read().splitlines() if line.strip()]
#     print(f'从股票池文件读取: {len(stock_list)} 只股票')
# except FileNotFoundError:
#     print(f'股票池文件不存在，使用全部A股')
#     stock_list = xtdata.get_stock_list_in_sector('沪深A股')

print(f'股票池数量: {len(stock_list)}')

#___________________________________________________________
# 判断是否需要下载数据
# 分钟线数据通常需要每天更新，所以这里简化判断逻辑
should_download = True

# 如果需要检查最新数据日期，可以取消下面的注释
# if new_data_time == today_str:
#     print('分钟线数据已更新到最新，跳过下载')
#     should_download = False

if should_download:
    print(f'本地最新数据日期: {new_data_time if new_data_time else "无数据"}')
    print(f'当前日期: {today_str}')
    print('='*60)
    print('注意：分钟线数据量很大，下载可能需要很长时间！')
    print('建议：')
    print('1. 首次下载建议设置较近的起始日期（如最近1-3个月）')
    print('2. 使用增量下载模式，只下载缺失的数据')
    print('3. 可以分批下载，先下载部分股票测试')
    print('='*60)
    
    # 设置起始日期（可以根据需要修改）
    # 分钟线数据量很大，建议不要设置太早的日期
    # 首次下载建议从最近1-3个月开始
    start_time = '20251008'  # 可以修改为更早的日期，格式：'YYYYMMDD'
    # start_time = ''  # 空字符串表示从最早开始下载（不推荐，数据量太大）
    
    print(f'\n下载时间范围: {start_time if start_time else "最早"} 至最新日期')
    print(f'周期: 1分钟')
    print(f'股票数量: {len(stock_list)} 只')
    
    # 询问确认（可选，如果不想交互可以注释掉）
    # user_input = input('\n确认开始下载？(y/n): ')
    # if user_input.lower() != 'y':
    #     print('已取消下载')
    #     exit(0)
    
    # 下载所需历史数据
    # 注意：xtdata.download_history_data 的参数顺序是：stock, period, start_time, end_time, incrementally
    print('\n开始逐个股票下载分钟线数据...')
    print('这可能需要很长时间，请耐心等待...\n')
    
    success_count = 0
    fail_count = 0
    start_download_time = datetime.now()
    
    for i, stock in enumerate(stock_list):
        try:
            # 使用位置参数调用
            # 参数：stock, period='1m', start_time='', end_time='', incrementally=True
            # period='1m' 表示分钟线数据
            xtdata.download_history_data(
                stock, 
                period='1m',  # 分钟线
                start_time=start_time,  # 从指定日期开始
                end_time='',  # 空字符串表示下载到最新日期
                incrementally=True  # 增量下载，只下载缺失的数据
            )
            success_count += 1
            
            # 每10只股票显示一次进度（分钟线数据下载较慢）
            if (i + 1) % 10 == 0:
                elapsed_time = (datetime.now() - start_download_time).total_seconds()
                avg_time_per_stock = elapsed_time / (i + 1)
                remaining_stocks = len(stock_list) - (i + 1)
                estimated_remaining_time = avg_time_per_stock * remaining_stocks
                
                print(f'进度: {i + 1}/{len(stock_list)} 只股票 | '
                      f'成功: {success_count} | 失败: {fail_count} | '
                      f'预计剩余时间: {int(estimated_remaining_time/60)} 分钟')
        except Exception as e:
            fail_count += 1
            if fail_count <= 10:  # 只打印前10个错误
                print(f'下载 {stock} 失败: {e}')
    
    # 下载完成统计
    total_time = (datetime.now() - start_download_time).total_seconds()
    print('\n' + '='*60)
    print('下载完成！')
    print(f'总耗时: {int(total_time/60)} 分钟 {int(total_time%60)} 秒')
    print(f'成功: {success_count} 只')
    print(f'失败: {fail_count} 只')
    print(f'成功率: {success_count/len(stock_list)*100:.2f}%')
    print('='*60)
    
    print('\n分钟线数据下载完成！')
    print('提示：可以使用 xtdata.get_local_data() 来验证数据是否下载成功')

