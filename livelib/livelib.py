from easytrader.log import logger
from easytrader.model import Balance, Position, Entrust, Deal
import pandas as pd
import math
import akshare as ak

def stock_zh_a_spot_em():
    logger.info(f"获取价格快照...")
    df = ak.stock_zh_a_spot_em()
    df = df[['代码', '名称', '最新价']]
    df = df.rename(columns={'代码': '证券代码',
                            '名称': '证券名称'})
    return df


def get_vol(m, price):
    vol = m.user.get_balance()[0].enable_balance / price // 100 * 100
    vol = min(500, vol)
    if vol < 500:
        logger.info(f"不足500股")
        return 0 # 不足买入500
    return vol

def print_state(m):
    print("\n=====================================================", end='')
    print("\n=                    当前状态                       =", end='')
    print("\n=====================================================")
    print("\n账户===============")
    balance = m.user.get_balance()[0]
    balance: Balance
    print(balance)
    print("\n持仓===============")
    data_position = {
        '证券代码': [],
        '证券名称': [],
        '持仓数量': [],
        '可用数量': [],
        '成本价': [],
        '当前价': [],
        '最新市值': [],
        '盈亏': [],
        '盈亏%': [],
    }
    pnl_sum = 0
    for p in m.user.get_position():
        p: Position
        if p.current_amount != 0:
            pnl = (p.last_price - p.cost_price) * p.current_amount
            pnl_sum += pnl
            pnl_pct = p.last_price / p.cost_price - 1
        else: # 已卖出的当日还在持仓列表中
            pnl = 0
            pnl_pct = 0
        data_position['证券代码'].append(p.stock_code)
        data_position['证券名称'].append(p.stock_name)
        data_position['持仓数量'].append(p.current_amount)
        data_position['可用数量'].append(p.enable_amount)
        data_position['成本价'].append(p.cost_price)
        data_position['当前价'].append(p.last_price)
        data_position['最新市值'].append(p.market_value)
        data_position['盈亏'].append(pnl)
        data_position['盈亏%'].append(pnl_pct)
    print(pd.DataFrame(data_position))
    print(f"当前盈亏 {pnl_sum:.2f} 当前盈亏% {pnl_sum / balance.asset_balance:.2%}")


    print("\n当日委托===========")
    data_entrust = {
        '委托时间':[],
        '证券代码':[],
        '证券名称':[],
        '委托方向':[],
        '委托数量':[],
        '委托状态':[],
        '委托价格':[],
    }
    for e in m.user.get_entrust():
        e: Entrust
        data_entrust['委托时间'].append(e.report_time)
        data_entrust['证券代码'].append(e.stock_code)
        data_entrust['证券名称'].append(e.stock_name)
        data_entrust['委托方向'].append(e.bs_type)
        data_entrust['委托数量'].append(e.entrust_amount)
        data_entrust['委托状态'].append(e.entrust_status)
        data_entrust['委托价格'].append(e.entrust_price)
    df_entrust = pd.DataFrame(data_entrust)
    df_spot = stock_zh_a_spot_em()
    df_entrust = pd.merge(df_entrust, df_spot[['证券代码', '最新价']], on='证券代码', how='left')
    df_entrust['价差'] = df_entrust['最新价'] - df_entrust['委托价格']
    df_entrust['PNL'] = df_entrust['价差'] * df_entrust['委托数量']
    df_entrust.loc[df_entrust['委托方向'] == 'S', 'PNL'] = df_entrust['PNL'] * -1
    print(df_entrust)
    print(f"买入收益 {df_entrust.loc[df_entrust['委托方向'] == 'B', 'PNL'].sum():.2f}")
    print(f"卖出收益 {df_entrust.loc[df_entrust['委托方向'] == 'S', 'PNL'].sum():.2f}")
    print("\n未成交==========")
    print(df_entrust[df_entrust['委托状态'] == '已报'])

    print("\n当日成交===========")
    data_deal = {
        '成交时间': [],
        '证券代码': [],
        '证券名称': [],
        '委托方向': [],
        '成交数量': [],
        '成交价格': [],
        '成交金额': [],
        '委托编号': [],
        '成交编号': [],
    }
    for d in m.user.get_current_deal():
        d: Deal
        data_deal['成交时间'].append(d.deal_time)
        data_deal['证券代码'].append(d.stock_code)
        data_deal['证券名称'].append(d.stock_name)
        data_deal['委托方向'].append(d.bs_type)
        data_deal['成交数量'].append(d.deal_amount)
        data_deal['成交价格'].append(d.deal_price)
        data_deal['成交金额'].append(d.deal_amount * d.deal_price)
        data_deal['委托编号'].append(d.deal_no)
        data_deal['成交编号'].append(d.entrust_no)
    df_deal = pd.DataFrame(data_deal)
    df_deal = pd.merge(df_deal, df_spot[['证券代码', '最新价']], on='证券代码', how='left')
    df_deal['价差'] = df_deal['最新价'] - df_deal['成交价格']
    df_deal['PNL'] = df_deal['价差'] * df_deal['成交数量']
    print(df_deal)
    print(f"买入收益 {df_deal.loc[df_deal['委托方向'] == 'B', 'PNL'].sum():.2f}")
    print(f"卖出收益 {df_deal.loc[df_deal['委托方向'] == 'S', 'PNL'].sum():.2f}")

def in_entrust(m, stock_code):
    for e in m.user.get_entrust():
        if e.stock_code == stock_code:
            logger.info(f"{stock_code} 已在委托中")
            return True
    return False

def in_deal(m, stock_code):
    for d in m.user.get_current_deal():
        if d.stock_code == stock_code:
            return True
    return False

def get_vol_price(m, wt, price):
    price = price * 0.985
    price = float(f"{price:.2f}")
    asset = m.user.get_balance()[0].asset_balance
    n_vol = 0

    while True:
        vol = asset * wt / price // 100 * 100 - n_vol * 100
        logger.info(f"asset {asset:.2f} wt {wt:.2f} {price:.2f} vol {vol}")
        if vol <= 0:
            logger.info(f"asset * wt {asset*wt:.2f} 不足购买100股 asset_balence {asset:.2f} price {price:.2f}")
            logger.info(f"尝试使用剩余可用...")
            enable_balance = m.user.get_balance()[0].enable_balance
            vol = enable_balance / price // 100 * 100 - n_vol * 100
            if vol <= 0:
                logger.info(f"仍然不足 enable_balance {enable_balance:.2f} price {price:.2f}")
                return 0, 0
        
        value = vol * price
        enable_balance = m.user.get_balance()[0].enable_balance
        if value <= enable_balance: # 现金能否成交，如果不能则减少股数
            break
        else:
            logger.info(f"value {value:.2f} > enable_balance {enable_balance:.2f}, 重新计算股数")
            n_vol += 1

    logger.info(f"vol {vol} price {price}")
    return vol, price
    # n = math.ceil(500 / vol) # 委托更低价格，减少跟踪组合手续费差距
    # logger.info(f"n {n} price {price} price' {price - 0.01 * n * 2}")

    # return vol, price - 0.01 * n * 2

def get_vol(m, price):
    vol = m.user.get_balance()[0].enable_balance / price // 100 * 100
    vol = min(500, vol)
    if vol < 500:
        logger.info(f"不足500股")
        return 0 # 不足买入500
    return vol

def get_position(m, stock_code):
    for p in m.user.get_position():
        if p.stock_code == stock_code:
            return p
    logger.info(f"{stock_code} 没有持仓")
    return None
