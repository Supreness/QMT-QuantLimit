#coding:utf-8

import numpy as np
from xtquant import xtdata
#xtdata.reconnect(port=58612)
def init(C):
    # init handlebar函数的入参是ContextInfo对象 可以缩写为C
    # 设置测试标的为主图品种
    # C.stock= C.stockcode + '.' +C.market
    C.stock = C._param.get('trade_stock','600050.SH')
    # line1和line2分别为两条均线期数
    # C.line1=34   #快线参数
    # C.line2=89   #慢线参数
    C.line1 = C._param.get('n1', 25)  # 快线参数
    C.line2 = C._param.get('n2', 120)  # 慢线参数
    # accountid为测试的ID 回测模式资金账号可以填任意字符串
    C.accountid = "testS"
    print('C.line1: ',C.line1, 'C.line2: ',C.line2)

def handlebar(C):
    # 当前k线日期
    bar_date = timetag_to_datetime(C.get_bar_timetag(C.barpos), '%Y%m%d%H%M%S')
    # 回测不需要订阅最新行情使用本地数据速度更快 指定subscribe参数为否. 如果回测多个品种 需要先下载对应周期历史数据
    local_data = C.get_market_data_ex(['close'], [C.stock], end_time=bar_date, period=C.period,
                                      count=max(C.line1, C.line2), subscribe=False)
    close_list = list(local_data[C.stock].iloc[:, 0])
    # 将获取的历史数据转换为DataFrame格式方便计算
    # 如果目前未持仓，同时快线穿过慢线，则买入8成仓位
    if len(close_list) < 1:
        print(bar_date, '行情不足 跳过')
    line1_mean = round(np.mean(close_list[-C.line1:]), 2)
    line2_mean = round(np.mean(close_list[-C.line2:]), 2)
    # print(f"{bar_date} 短均线{line1_mean} 长均线{line2_mean}")
    account = get_trade_detail_data('test', 'stock', 'account')
    account = account[0]
    available_cash = int(account.m_dAvailable)
    holdings = get_trade_detail_data('test', 'stock', 'position')
    holdings = {i.m_strInstrumentID + '.' + i.m_strExchangeID: i.m_nVolume for i in holdings}
    holding_vol = holdings[C.stock] if C.stock in holdings else 0
    if holding_vol == 0 and line1_mean > line2_mean:
        vol = int(available_cash / close_list[-1] / 100) * 100
        # 下单开仓
        passorder(23, 1101, C.accountid, C.stock, 5, -1, vol, '', 0, '', C)
    # print(f"{bar_date} 开仓")
    # C.draw_text(1, 1, '开')
    # 如果目前持仓中，同时快线下穿慢线，则全部平仓
    elif holding_vol > 0 and line1_mean < line2_mean:
        # 状态变更为未持仓
        C.holding = False
        # 下**仓
        passorder(24, 1101, C.accountid, C.stock, 5, -1, holding_vol, '', 0, '', C)
    # print(f"{bar_date} 平仓")
    # C.draw_text(1, 1, '平')


if __name__ == '__main__':

    import sys
    from xtquant.qmttools import run_strategy_file

    # 回测时
    trade_mode = 'backtest'
    quote_mode = 'history'

    #实盘时/模拟时
    # trade_mode = 'simulation'
    # quote_mode = 'realtime'


    # 回测参数设置
    detail = {
        "asset" : 100_0000.0                     # 初始资金
        , "margin_ratio" : 0.05             # 保证金比例（期货用）

        , "slippage_type" :1              # 滑点类型 0 按最小变动价跳数；  1：按固定值；2：按成交额比例。
        , "slippage" : 1                   # 滑点 说明 当slippage_type=0,slippage=1,表示每股滑点是1跳（下100股会直接造成100*0.01=1元亏损）；slippage_type=1,slippage=1 表示每股滑点是1元（下100股会直接造成100元亏损）；slippage_type=2,slippage=0.05 表示每笔交易的滑点比例为5%
        , "max_vol_rate" : 0.0              #最大成交比例
        # comsisson_type说明 0 按成交额比例； 1 按固定值
        # 该值影响 open_commission close_commission close_today_commission
        , "comsisson_type" : 0               #手续费类型 0 按成交额比例； 1 按固定值
        # 买入印花税， 单位永远是比例，0.0001表示万 1的手续费 # 股票生效，期货不生效
        , "open_tax" : 0.0001

        # 卖出印花税，单位永远是比例， 0.0001表示万 1的手续费 # 股票生效，期货不生效
        , "close_tax" : 0   

        # 最小手续费  #单位永远是元 设置成1 股票表示每股扣除1元,# 股票生效，期货不生效
        , "min_commission" : 0       

        # 买入/开仓手续费  comsisson_type选0 ，0.0001表示万 1的手续费 comsisson_type选1 单位就是元。 股票、期货生效
        # 单位是元时，股票表示每股扣1元，期货表示每手1元
        , "open_commission" :0#  0.00085      

        # 卖出手续费 comsisson_type选0 ，0.0001表示万 1的手续费 comsisson_type选1 单位就是元。 股票表示卖出、期货表示平昨
        # 单位是元时，股票表示每股扣1元，期货表示每手1元
        , "close_commission" : 0 

        # 平今手续费  comsisson_type选0 ，0.0001表示万 1的手续费 comsisson_type选1 单位就是元。股票不生效,期货表示平今
        # 单位是元时，股票表示每股扣1元，期货表示每手1元
        , "close_today_commission" :  0  

        # 业绩比较基准
        , "benchmark" : '000300.SH'     

    }
    # 回测参数设置
    param = {
    'stock_code': '000300.SH',  # 驱动handlebar的代码, # 注意，如果没有下载历史数据，则handlebar可能无法运行
    'period': '1d',  # 策略执行周期 即主图周期
    'start_time': '2015-01-09 00:00:00',  # 注意格式，不要写错
    'end_time': '2024-08-30 00:00:00',  # 注意格式，不要写错
    # handlebar模式，'realtime':仅实时行情（不调用历史行情的handlebar）,'history':仅历史行情, 'all'：所有，即history+realtime
    'trade_mode': trade_mode,  # simulation': 模拟, 'trading':实盘, 'backtest':回测
    'quote_mode': quote_mode,
    # 回测参数
    'backtest':detail,
     #还可以传入自定义参数
    'n1' :5,
    'n2':20,
    'trade_stock': '600519.SH'
    }
  
    user_script = sys.argv[0]  # 当前脚本路径，相对路径，绝对路径均可，此处为绝对路径的方法

    print(user_script)
    result = run_strategy_file(user_script, param=param)
    print(result)
    r1 = result.get_backtest_index()
    r2 = result.get_group_result()
    print(r1)
    print(r2)
