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

local_data = xtdata.get_local_data(field_list=['open',],
                           stock_list=['600795.SH'],
                           count=2,
                           period='1d')['600795.SH']
if len(local_data) == 0:
    new_data_time = ''
else:
    new_data_time = data_000001.index[-1]

sector_list = xtdata.get_sector_list()
if not sector_list:
    xtdata.download_sector_data()

#___________________________________________________________
# 指定文件夹路径
folder_path = './配置文件'


stock_list = xtdata.get_stock_list_in_sector('沪深A股')

# 获取当天日期并转换为'YYYYMMDD'格式
today_str = datetime.now().strftime('%Y%m%d')


# if "15:00">  current_time > "09:15":
#     trader_data = data_000001.index[0]
# else:
#     trader_data = data_000001.index[-1]

#___________________________________________________________
if new_data_time == today_str:
    print('数据已更新，跳过下载')
else:
    print('开始下载数据,需要花费5分钟')
    # 下载所需历史数据(提前运行)
    xtdata.download_history_data(stock_list='沪深A股', period='1d', start_time='20230101')
    print('数据下载完成')

