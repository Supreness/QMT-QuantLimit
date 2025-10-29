'''
筛选出市值介于7-23亿的股票，剔除退市、ST、北交所和科创板；
结合其他财务指标，选取其中PE最低的5只股票；
每天开盘买入，持有五个交易日，然后再次筛选股票；
如果持仓股在新筛选的股票中则继续持有，否则调仓
'''
from jqdata import get_trade_days


# 初始化函数，设定要操作的股票、基准等等
def initialize(context):
    # 设置日志级别为error
    log.set_level('order', 'error')
    # 设定中证1000作为基准
    set_benchmark('000852.XSHG')
    # True为开启动态复权模式，使用真实价格交易
    set_option('use_real_price', True)
    # 设置是否开启避免未来数据模式
    # set_option('avoid_future_data', True)
    # 设置滑点
    set_slippage(FixedSlippage(0.02))
    # 设定成交量比例
    set_option('order_volume_ratio', 1)
    # 股票类交易手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, \
                             open_commission=0.0003, close_commission=0.0003, \
                             close_today_commission=0, min_commission=5), type='stock')
    # 持仓数量
    g.name = '太平洋钓鱼-PE'
    g.stocknum = 10
    # 交易日计时器
    g.days = 0
    # 调仓频率
    g.refresh_rate = 5
    g.is_high = False
    g.stoploss_rate = 0.90
    # 在全局变量中增加涨停检查字典
    g.zt_check_stocks = {}  # 格式：{stock: next_check_date}
    run_daily(pre_check_stocks, time='before_open', reference_security='000300.XSHG')
    # 运行函数
    # run_daily(check_high_price, time='9:30', reference_security='000300.XSHG')
    run_daily(trade, time='09:45', reference_security='000300.XSHG')
    run_daily(check_volume, time='14:56', reference_security='000300.XSHG')
    # run_daily(handle_zt_check, time='14:56', reference_security='000300.XSHG')
    run_daily(check_zt_after_close, time='after_close', reference_security='000300.XSHG')


def pre_check_stocks(context):
    g.select_stocks = check_stocks(context)[:g.stocknum]
    if g.days % g.refresh_rate == 0:
        trade_info_text = f"当前策略：{g.name}，当前日期：{context.current_dt.date()}\n"
        new_stock_names = [get_security_info(stock).display_name for stock in g.select_stocks]
        trade_info_text = trade_info_text + '今日预选股票池代码：' + ', '.join(g.select_stocks) + '\n'
        trade_info_text = trade_info_text + '今日预选股票池名称：' + ', '.join(new_stock_names) + '\n'
        send(trade_info_text)


# 选出小市值股票
def check_stocks(context):
    # 先过滤停牌、退市和ST股票
    all_codes = get_all_securities('stock').index
    security_list = filter_stocks(all_codes)
    # 设定查询条件
    q = query(
        valuation.code,
        valuation.market_cap
    ).filter(
        # (valuation.code.startswith('60') | valuation.code.startswith('00') | valuation.code.startswith('30')),
        (valuation.code.startswith('00') | valuation.code.startswith('30')),
        valuation.market_cap.between(8, 50),
        valuation.pe_ratio.between(0, 50),
        income.net_profit > 0,
        valuation.code.in_(security_list)
    ).order_by(
        valuation.market_cap.asc()
    ).limit(g.stocknum)

    # 获取昨日日期
    yesterday = context.previous_date
    df = get_fundamentals(q)
    buylist = list(df['code'])
    buylist = buylist[:g.stocknum]
    return buylist


def stop_loss(context, current_data):
    stoploss_sold_stocks = []
    # 亏损幅度达到10个点止损
    for stock in context.portfolio.positions.keys():
        # 获取持仓成本和当前价格
        position = context.portfolio.positions[stock]
        cost_price = position.avg_cost  # 持仓成本价
        current_price = current_data[stock].last_price  # 当前价格

        # 当亏损超过10%时止损
        if current_price < g.stoploss_rate * cost_price:
            # 使用统一卖出方法
            execute_sell_orders(context, [stock], "亏损10个点止损")
            # 记录卖出日期
            # g.sold_stocks[stock] = context.current_dt.date()
            stoploss_sold_stocks.append(stock)
    return stoploss_sold_stocks


# 交易函数
def trade(context):
    current_data = get_current_data()
    trade_info_text = ""
    stoploss_sold_stocks = []  # 记录调仓日当天因止损卖出的股票列表

    if g.is_high:
        return

    stoploss_sold_stocks = stop_loss(context, current_data)


    if g.days % g.refresh_rate == 0:
        # 获取当前持仓股票列表
        current_holdings = list(context.portfolio.positions.keys())

        # 判断是否需要调仓及处理止损卖出后当天不能买入的情况
        stocks_to_sell = []
        stocks_to_buy = []
        for stock in current_holdings:
            if stock not in g.select_stocks:
                stocks_to_sell.append(stock)
            elif stock in stoploss_sold_stocks:
                continue  # 如果当天因止损卖出过该股票，调仓日当天不再买入

        # 待买入的新股票
        for stock in g.select_stocks:
            if stock not in current_holdings and stock not in stoploss_sold_stocks:
                stocks_to_buy.append(stock)

        # 卖出股票
        execute_sell_orders(context, stocks_to_sell, "定期调仓卖出")
        # 分配资金买入新股票
        if len(stocks_to_buy) > 0:
            cash_amount = context.portfolio.total_value / g.stocknum
            execute_buy_orders(context, stocks_to_buy, cash_amount, 1, "定期调仓")

        # 天计数加一
        g.days = 1

    else:
        g.days += 1


# def check_high_price(context):
#     g.is_high = False
#     current_data = get_current_data()
#     df_volume = get_bars('000001.XSHG', count=2, unit='1d', fields=['close'], include_now=True, df=True)
#     is_high = df_volume['close'].values[-1] > 1.05 * df_volume['close'].values[0]
#     for stock in context.portfolio.positions:
#         if current_data[stock].paused == True:
#             continue
#         if context.portfolio.positions[stock].closeable_amount == 0:
#             continue
#         if is_high:
#             log.info("[%s]天量，卖出" % stock)
#             position = context.portfolio.positions[stock]
#             order_target_value(stock, 0)
#             g.is_high = True

# ======================= 卖出操作统一封装 =======================
def execute_sell_orders(context, sell_list, reason=""):
    """执行卖出操作的统一方法
    :param context: 策略上下文
    :param sell_list: 待卖出股票列表
    :param reason: 卖出原因描述
    """
    if not sell_list:
        return

    current_data = get_current_data()
    trade_info = []

    force_sell = (reason == "沪指高开清仓")  # 判断是否强制卖出

    for stock in sell_list:
        try:
            # if not force_sell and stock in g.zt_check_stocks:
            #     log.info(f"{stock} 处于涨停监控中，暂不执行卖出")
            #     continue

            # 基础检查
            if not force_sell:
                if not check_sellable(context, stock, current_data):
                    continue
            # 执行回测卖出
            order_target_value(stock, 0)

            # 记录交易信息
            stock_name = get_security_info(stock).display_name
            trade_info.append(f"{stock} {stock_name}")
        except Exception as e:
            log.error(f"卖出失败 {stock}: {str(e)}")

    # 发送交易通知
    if trade_info:
        send_message = [
            f"【卖出操作 {context.current_dt.date()}】",
            f"卖出原因: {reason}",
            f"卖出数量: {len(trade_info)} 只",
            "卖出明细:",
            "\n".join(trade_info)
        ]
        send('\n'.join(send_message))

# ======================= 买入操作统一封装 =======================
def execute_buy_orders(context, buy_list, cash, type=1, reason=""):
    """执行买入操作的统一方法
    :param context: 策略上下文
    :param buy_list: 待买入股票列表
    :param cash: 买入资金
    :param type: 买入原因类型
    :param reason: 买入原因描述
    """
    if not buy_list:
        return

    # 获取当前市场数据
    current_data = get_current_data()

    trade_info = []
    for stock in buy_list:
        # 基础检查
        if not check_buy_able(context, stock, current_data):
            continue

        # 执行买入操作
        try:
            # 回测环境操作
            order_value(stock, cash)

            # 实盘环境操作
            # if is_real_trade():
            #     submit_real_buy(stock, cash)

            # 记录交易信息
            stock_name = get_security_info(stock).display_name
            trade_info.append(f"{stock} {stock_name}")

            # 补仓买入需要更新空位数量
            if type == 2:
                g.empty_slots -= 1
                if g.empty_slots == 0:
                    break

        except Exception as e:
            log.error(f"买入失败 {stock}: {str(e)}")

    # 发送交易通知
    if trade_info:
        send_message = [
            f"【买入操作 {context.current_dt.date()}】",
            f"买入原因: {reason}",
            f"买入数量: {len(trade_info)} 只",
            "买入明细:",
            "\n".join(trade_info)
        ]
        send('\n'.join(send_message))

def check_buy_able(context, stock, current_data):
    """检查股票是否可买"""
    # 基础状态检查
    if current_data[stock].paused:
        return False
    if current_data[stock].last_price >= current_data[stock].high_limit:
        return False
    if current_data[stock].last_price <= current_data[stock].low_limit:
        return False
    # 持仓数量检查
    if len(context.portfolio.positions) >= g.stocknum:
        return False
    return True

def check_sellable(context, stock, current_data):
    """检查股票是否可卖"""
    # 基础状态检查
    if current_data[stock].paused:
        return False
    # 无可用持仓
    if context.portfolio.positions[stock].closeable_amount <= 0:
        return False
    if current_data[stock].last_price >= current_data[stock].high_limit:
        send(f'持仓股票{stock}已涨停，继续持有')
        return False
    return True

# 检查是否放出天量
def check_volume(context):
    # 获取当前持仓的所有股票
    positions = context.portfolio.positions
    stock_to_sell = []

    for stock in positions:
        # 获取股票的近90天成交量数据
        volume_data = get_bars(stock, count=90, unit='1d', fields=['volume'], include_now=True, df=True)

        # 获取今天的成交量
        today_vol = volume_data['volume'].iloc[-1]

        # 排除今天的成交量数据，计算过去89天的最大成交量
        max_volume = volume_data['volume'].iloc[:-1].max()

        # 判断今天的成交量是否为过去89天的最大值
        if today_vol > max_volume:
            # execute_sell_orders(context, [stock], "天量卖出")
            stock_to_sell.append(stock)
            # g.empty_slots += 1
            # g.sold_stocks[stock] = context.current_dt.date()
    execute_sell_orders(context, stock_to_sell, "天量卖出")

    handle_zt_check(context)

def check_zt_after_close(context):
    """收盘后检测涨停股票"""
    current_data = get_current_data()
    # 清空前一天数据
    g.zt_check_stocks.clear()

    # 获取当日所有持仓
    for stock in context.portfolio.positions.keys():
        # 获取当日K线
        today_bar = get_bars(stock, count=1, unit='1d', fields=['close','high_limit'], include_now=True)
        if len(today_bar) == 0:
            continue

        close_price = today_bar['close'][0]
        high_limit = today_bar['high_limit'][0]

        # 判断当日是否涨停（收盘价等于涨停价）
        if close_price >= high_limit:
            # 获取下一交易日
            next_date = get_trade_days(start_date=context.current_dt.date(), count=2)[-1]
            g.zt_check_stocks[stock] = next_date
            log.info(f"涨停股票加入监控：{stock}，下次检查日期：{next_date}")


def handle_zt_check(context):
    """执行涨停股票检查"""
    current_data = get_current_data()
    to_remove = []
    to_add = {}

    for stock, check_date in g.zt_check_stocks.items():
        # 只处理当天需要检查的
        if check_date != context.current_dt.date():
            continue

        # 获取当前价格
        if current_data[stock].paused:
            continue

        # 获取最新价和涨停价
        last_price = current_data[stock].last_price
        high_limit = current_data[stock].high_limit

        # 判断是否连续涨停
        if last_price < high_limit:
            log.info(f"涨停断板：{stock} 现价：{last_price} 涨停价：{high_limit}")
            execute_sell_orders(context, [stock], "涨停断板卖出")
            to_remove.append(stock)
            # g.empty_slots += 1
            # g.sold_stocks[stock] = context.current_dt.date()
        else:
            # 继续监控下一个交易日
            next_date = get_trade_days(start_date=check_date, count=2)[-1]
            to_add[stock] = next_date
            log.info(f"恭喜连板：{stock}，下次检查：{next_date}")
            to_remove.append(stock)

    # 更新监控列表
    for stock in to_remove:
        del g.zt_check_stocks[stock]
    g.zt_check_stocks.update(to_add)


def filter_stocks(security_list):
    """综合过滤停牌、退市和ST股票"""
    current_data = get_current_data()
    return [stock for stock in security_list
            if not current_data[stock].paused  # 排除停牌
            and '退' not in current_data[stock].name  # 排除退市
            and not current_data[stock].is_st]  # 排除ST股


def send(msg):
    log.info(msg)