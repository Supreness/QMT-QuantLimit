import json
from xtquant import xtdata
import pandas as pd
from datetime import datetime
import os
import glob
xtdata.enable_hello = False

# 获取当前时间
current_time = datetime.now().strftime('%H:%M')
today_str = datetime.now().strftime('%Y%m%d')

# 检查本地最新数据日期
try:
    local_data = xtdata.get_local_data(field_list=['open',],
                               stock_list=['600795.SH'],
                               count=2,
                               period='1d')['600795.SH']
    if len(local_data) == 0:
        new_data_time = ''
    else:
        # 修复：使用 local_data 而不是 data_000001，并转换为字符串格式
        # 如果index已经是Timestamp，直接转换；如果是其他格式，先转换为Timestamp
        last_date = local_data.index[-1]
        if isinstance(last_date, pd.Timestamp):
            new_data_time = last_date.strftime('%Y%m%d')
        else:
            new_data_time = pd.Timestamp(last_date).strftime('%Y%m%d')
except Exception as e:
    print(f'检查本地数据日期时出错: {e}')
    new_data_time = ''

# 下载板块数据（如果需要）
sector_list = xtdata.get_sector_list()
if not sector_list:
    xtdata.download_sector_data()

#___________________________________________________________
# 获取股票列表
stock_list = xtdata.get_stock_list_in_sector('沪深A股')
print(f'股票池数量: {len(stock_list)}')

#___________________________________________________________
# 判断是否需要下载数据
if new_data_time == today_str:
    print('数据已更新到最新，跳过下载')
else:
    print(f'本地最新数据日期: {new_data_time if new_data_time else "无数据"}')
    print(f'当前日期: {today_str}')
    print('开始下载历史数据，这可能需要较长时间...')
    
    # 设置起始日期（可以根据需要修改）
    start_time = '20230101'  # 可以修改为更早的日期，格式：'YYYYMMDD'
    
    print(f'下载时间范围: {start_time} 至最新日期')
    
    # 下载所需历史数据
    # 注意：xtdata.download_history_data 的参数顺序是：stock, period, start_time, end_time, incrementally
    # 根据策略数据初始化.py中的用法，使用位置参数
    print('开始逐个股票下载数据...')
    success_count = 0
    fail_count = 0
    
    for i, stock in enumerate(stock_list):
        try:
            # 使用位置参数调用，与策略数据初始化.py中的用法一致
            # 参数：stock, period='1d', start_time='', end_time='', incrementally=True
            # 如果start_time为空字符串，会从最早开始下载
            # 如果end_time为空字符串，会下载到最新日期
            xtdata.download_history_data(
                stock, 
                period='1d', 
                start_time=start_time,  # 从指定日期开始
                end_time='',  # 空字符串表示下载到最新日期
                incrementally=True  # 增量下载，只下载缺失的数据
            )
            success_count += 1
            if (i + 1) % 100 == 0:
                print(f'已下载 {i + 1}/{len(stock_list)} 只股票...')
        except Exception as e:
            fail_count += 1
            if fail_count <= 10:  # 只打印前10个错误
                print(f'下载 {stock} 失败: {e}')
    
    print(f'下载完成: 成功 {success_count} 只, 失败 {fail_count} 只')
    
    print('历史数据下载完成！')

