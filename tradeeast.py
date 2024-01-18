import easyquant
from easyquant import DefaultLogHandler
from easytrader.model import Balance, Position, Entrust, Deal
import pandas as pd
from easytrader.log import logger
import math
from livelib import livelib

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 180)                       # 设置打印宽度(**重要**)

print('测试 DEMO')

# 东财
broker = 'eastmoney'

# 自己准备
# {
#     "user": "",
#     "password": ""#
# }
need_data = 'account.json'

log_type = 'file'

log_handler = DefaultLogHandler(name='测试', log_type=log_type, filepath='logs.log')

m = easyquant.MainEngine(broker,
                         need_data,
                         quotation='online',
                         # 1分钟K线
                         bar_type="1m",
                         log_handler=log_handler)
# m.is_watch_strategy = True  # 策略文件出现改动时,自动重载,不建议在生产环境下使用
# m.load_strategy()
# m.start()

livelib.print_state(m)

wt = 1 / 6 # 最多持仓x支股票

while True:
    prompt = input("\n输入指令\n1. B/S stock_code price 买入卖出\n2. 'p' 打印状态\n3. 'q' 退出\n")
    if len(prompt.split()) == 3:
        bs_type, stock_code, price = prompt.split() 
        price = float(price)
        print(bs_type, stock_code, price)
        if bs_type == 'b':
            # if not livelib.in_entrust(m, stock_code):
            if True:
                # vol = get_vol(price)
                vol, price = livelib.get_vol_price(m, wt, price)
                if vol == 0:
                    continue
                logger.info(f"买入 {stock_code} at {price} {vol}")
                m.user.buy(stock_code, price, vol)
        elif bs_type == 's':
            p = livelib.get_position(m, stock_code)
            if p is None:
                continue
            if p.enable_amount == 0:
                logger.info(f"不可卖出（今日买入/已委托）")
                continue
            logger.info(f"卖出 {stock_code} at {price} 全部股份")
            m.user.sell(stock_code, price, p.enable_amount)

    elif len(prompt.split()) == 1:
        if prompt == 'p':
            livelib.print_state(m)
        elif prompt == 'q':
            print("退出")
            break

# while True:



