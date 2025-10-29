import pandas as pd
from xtquant import xtdata
from datetime import datetime
import time
from lark.bot.send_msg import *


class SmallCapPEStrategy:
    def __init__(self):
        # 策略参数
        self.stock_num = 5  # 持仓股票数量
        self.refresh_rate = 5  # 调仓频率（交易日）
        self.days = 0  # 交易日计数器
        self.portfolio = {}  # 模拟持仓 {股票代码: 买入日期}
        self.market_cap_range = (7e8, 23e8)  # 市值范围7-23亿
        
        # 获取交易日历
        self.trading_dates = self.get_trading_dates(end_date=datetime.now().strftime("%Y%m%d"))
        self.current_date_timestamp = self.trading_dates[-1]
        self.current_date = datetime.fromtimestamp(int(self.trading_dates[-1])/1000).strftime("%Y%m%d")
        
        # 初始化数据
        self.all_stocks = xtdata.get_stock_list_in_sector('沪深A股')

        def on_progress(data):
            print(data)

        #xtdata.download_history_data2(stock_list=self.all_stocks, period='1d', start_time='20240101', end_time=self.current_date, callback=on_progress)
        #xtdata.download_financial_data2(self.all_stocks, ["Balance","Income"], start_time='20240101', end_time=self.current_date, callback=on_progress)

        # 发送初始化消息
        self.send_lark_message("策略初始化完成", 
                              f"策略参数:\n持仓数量: {self.stock_num}\n调仓频率: 每{self.refresh_rate}个交易日\n市值范围: {self.market_cap_range[0] / 1e8}-{self.market_cap_range[1] / 1e8}亿")

    def get_trading_dates(self, start_date="20240101", end_date="20241231"):
        """获取交易日历"""
        return xtdata.get_trading_dates("SH", start_date, end_date)

    def filter_stocks(self):
        """
        筛选符合条件的股票：
        1. 市值介于7-23亿
        2. 剔除ST、退市、北交所和科创板股票
        3. 选择PE最低的5只股票
        """
        valid_stocks = []
        yesterday = datetime.fromtimestamp(self.get_previous_trading_date(self.current_date_timestamp)/1000).strftime("%Y%m%d")

        for stock in self.all_stocks:
            # 排除ST股
            stock_detail = xtdata.get_instrument_detail(stock)
            if not stock_detail:
                continue
                
            stock_name = stock_detail.get('InstrumentName', '')
            if 'ST' in stock_name or '*' in stock_name or '退' in stock_name:
                continue
            
            # 排除北交所(4/8开头)和科创板(688开头)
            if stock.startswith('4') or stock.startswith('8') or stock.startswith('688'):
                continue
            
            # 获取市值数据
                
            market_cap = stock_detail.get('PreClose')*stock_detail.get('TotalVolume')
            if not (self.market_cap_range[0] <= market_cap <= self.market_cap_range[1]):
                continue
            
            # 获取PE数据
            financial_data = xtdata.get_financial_data([stock], table_list=['Income'])
            if not financial_data or stock not in financial_data:
                continue

            #pe_ratio = financial_data[stock].get('Income', {}).get('net_profit_excl_min_int_inc', float('inf'))
           # if pd.isna(pe_ratio) or pe_ratio <= 0:
            #    continue
            
            valid_stocks.append({
                'stock': stock,
                'name': stock_name,
                'market_cap': market_cap,
                'pe_ratio': float('inf')
            })
        
        # 按PE升序排序，选择PE最低的5只股票
        valid_stocks.sort(key=lambda x: x['market_cap'])
        return valid_stocks[:self.stock_num]
    
    def get_previous_trading_date(self, date):
        """获取前一个交易日"""
        idx = self.trading_dates.index(date)
        return self.trading_dates[idx-1] if idx > 0 else date
    
    def rebalance_portfolio(self):
        """执行调仓操作（发送Lark消息代替实际交易）"""
        # 获取新股票池
        new_stocks = self.filter_stocks()
        new_stock_codes = [s['stock'] for s in new_stocks]
        
        # 确定需要卖出的股票
        stocks_to_sell = [stock for stock in self.portfolio if stock not in new_stock_codes]
        
        # 确定需要买入的股票
        stocks_to_buy = [stock for stock in new_stock_codes if stock not in self.portfolio]
        
        # 更新持仓
        for stock in stocks_to_sell:
            self.portfolio.pop(stock)
        
        for stock in stocks_to_buy:
            self.portfolio[stock] = self.current_date_timestamp
        
        # 准备消息内容
        message = f"【调仓操作】{self.current_date}\n"
        message += f"持仓天数: {self.days}天\n\n"
        
        if stocks_to_sell:
            sell_details = "\n".join([f"{stock} - {xtdata.get_instrument_detail(stock).get('InstrumentName', '')}" 
                                      for stock in stocks_to_sell])
            message += f"卖出股票({len(stocks_to_sell)}只):\n{sell_details}\n\n"
        else:
            message += "无卖出股票\n\n"
        
        if stocks_to_buy:
            buy_details = "\n".join([f"{s['stock']} - {s['name']} (PE: {s['pe_ratio']:.2f}, 市值: {s['market_cap']/1e8:.2f}亿)" 
                                    for s in new_stocks if s['stock'] in stocks_to_buy])
            message += f"买入股票({len(stocks_to_buy)}只):\n{buy_details}\n\n"
        else:
            message += "无买入股票\n\n"
        
        # 添加新持仓详情
        message += "新持仓:\n"
        for s in new_stocks:
            holding_days = (self.current_date_timestamp - self.portfolio.get(s['stock'], self.current_date_timestamp))/86400000 + 1
            message += f"{s['stock']} - {s['name']} (持有天数: {holding_days})\n"
        
        # 发送Lark消息
        self.send_lark_message("调仓操作通知", message)
    
    def send_lark_message(self, title, content):
        """发送消息到Lark"""
        try:
            response = send_normal_msg_to_group(title, content)
            print(f"Lark消息已发送: {response.code}")
        except Exception as e:
            print(f"发送Lark消息失败: {str(e)}")

    def run(self):
        """运行策略"""
        #
        # 调仓执行操作
        if self.days % self.refresh_rate == 0:
            self.rebalance_portfolio()
            self.days = 0  # 重置天数计数器

        # 非调仓日只发送持仓情况
        else:
            holding_info = "当前持仓:\n"
            for stock, buy_date in self.portfolio.items():
                holding_days = (self.current_date_timestamp - buy_date).days + 1
                stock_name = xtdata.get_instrument_detail(stock).get('InstrumentName', '')
                holding_info += f"{stock} - {stock_name} (持有天数: {holding_days}/{self.refresh_rate})\n"

            if holding_info:
                self.send_lark_message("持仓概览", holding_info)

            # 模拟交易日间隔
            time.sleep(1)

    def run_bact_test(self, start_date=None, end_date=None):
        return

# 运行策略
if __name__ == "__main__":
    # 确保数据已下载
    strategy = SmallCapPEStrategy()
    strategy.run()