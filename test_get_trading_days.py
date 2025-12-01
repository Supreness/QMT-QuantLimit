#coding:utf-8
"""
测试 get_trading_days 函数
验证交易日获取功能是否正常
"""

from xtquant import xtdata
import pandas as pd
from datetime import datetime

xtdata.enable_hello = False

def get_trading_days(start_date, end_date):
    """
    获取交易日列表
    
    参数:
    start_date: 开始日期，格式 'YYYYMMDD'
    end_date: 结束日期，格式 'YYYYMMDD'
    
    返回:
    交易日列表，格式 ['YYYYMMDD', ...]
    """
    # 将日期格式从 'YYYYMMDD' 转换为 'YYYY-MM-DD'
    start_date_formatted = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"
    end_date_formatted = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"
    
    # 使用上证指数作为基准（更可靠，几乎不会停牌）
    # 也可以使用其他指数：'000300.SH'（沪深300）、'399001.SZ'（深证成指）等
    benchmark_stocks = ['000001.SH', '399001.SZ']  # 使用两个指数，确保至少有一个有数据
    
    trading_days = []
    
    for benchmark_stock in benchmark_stocks:
        try:
            # 获取基准指数的交易日数据
            benchmark_data = xtdata.get_market_data(
                stock_list=[benchmark_stock],
                period='1d',
                start_time=start_date_formatted,
                end_time=end_date_formatted,
                dividend_type='front_ratio',
                fill_data=False
            )
            
            if benchmark_stock in benchmark_data and len(benchmark_data[benchmark_stock]) > 0:
                # 获取交易日索引并转换为字符串格式
                trading_days = benchmark_data[benchmark_stock].index.tolist()
                trading_days = [pd.Timestamp(day).strftime('%Y%m%d') for day in trading_days]
                print(f'使用 {benchmark_stock} 获取到 {len(trading_days)} 个交易日')
                break
        except Exception as e:
            print(f'使用 {benchmark_stock} 获取交易日失败: {e}')
            continue
    
    if not trading_days:
        # 如果都失败了，尝试使用本地数据
        try:
            print('尝试使用本地数据获取交易日...')
            local_data = xtdata.get_local_data(
                field_list=['open'],
                stock_list=['000001.SH'],
                start_time=start_date_formatted,
                end_time=end_date_formatted,
                period='1d'
            )
            if '000001.SH' in local_data and len(local_data['000001.SH']) > 0:
                trading_days = local_data['000001.SH'].index.tolist()
                trading_days = [pd.Timestamp(day).strftime('%Y%m%d') for day in trading_days]
                print(f'使用本地数据获取到 {len(trading_days)} 个交易日')
        except Exception as e:
            print(f'使用本地数据获取交易日失败: {e}')
    
    if not trading_days:
        print(f'警告：无法获取交易日列表，请检查日期范围 {start_date} 至 {end_date}')
        print('提示：请确保已下载对应日期的历史数据')
    
    return trading_days


if __name__ == '__main__':
    print('='*60)
    print('测试 get_trading_days 函数')
    print('='*60)
    
    # 测试用例1：最近一个月
    print('\n测试用例1：最近一个月')
    start_date = '20241001'
    end_date = '20241031'
    print(f'日期范围: {start_date} 至 {end_date}')
    trading_days = get_trading_days(start_date, end_date)
    if trading_days:
        print(f'获取到 {len(trading_days)} 个交易日')
        print(f'第一个交易日: {trading_days[0]}')
        print(f'最后一个交易日: {trading_days[-1]}')
        print(f'前5个交易日: {trading_days[:5]}')
        print(f'后5个交易日: {trading_days[-5:]}')
    else:
        print('获取交易日失败！')
    
    # 测试用例2：最近一周
    print('\n' + '='*60)
    print('测试用例2：最近一周')
    start_date = '20241118'
    end_date = '20241122'
    print(f'日期范围: {start_date} 至 {end_date}')
    trading_days = get_trading_days(start_date, end_date)
    if trading_days:
        print(f'获取到 {len(trading_days)} 个交易日')
        print(f'交易日列表: {trading_days}')
    else:
        print('获取交易日失败！')
    
    # 测试用例3：回测脚本中使用的日期范围
    print('\n' + '='*60)
    print('测试用例3：回测脚本中的日期范围')
    start_date = '20251008'
    end_date = '20251122'
    print(f'日期范围: {start_date} 至 {end_date}')
    trading_days = get_trading_days(start_date, end_date)
    if trading_days:
        print(f'获取到 {len(trading_days)} 个交易日')
        print(f'第一个交易日: {trading_days[0]}')
        print(f'最后一个交易日: {trading_days[-1]}')
        print(f'交易日数量: {len(trading_days)}')
    else:
        print('获取交易日失败！')
        print('提示：如果日期是未来日期，请使用已过去的日期进行测试')
    
    print('\n' + '='*60)
    print('测试完成！')
    print('='*60)

