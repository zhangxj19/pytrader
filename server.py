import easyquant
from easyquant import DefaultLogHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import threading
import re

from urllib.parse import unquote

import livelib.livelib as livelib
from easytrader.log import logger

pattern_order = ".*厚积薄发.*(买入|卖出).*?([0-9]{6}).*?(\d+\.\d+)元.*"
broker = 'eastmoney'
wt = 1 / 6
need_data = 'account.json'
log_type = 'file'
log_handler = DefaultLogHandler(name='测试', log_type=log_type, filepath='logs.log')

# 定义处理请求的类
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 处理GET请求
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Hello, GET request!')

    def do_POST(self):
        # 处理POST请求
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Hello, POST request!')
        msg = unquote(post_data)
        logger.info(f'POST data: {msg}')

        is_match = re.match(pattern_order, msg)
        if is_match:
            if len(is_match.groups()) == 3:

                m = easyquant.MainEngine(broker,
                                        need_data,
                                        quotation='online',
                                        # 1分钟K线
                                        bar_type="1m",
                                        log_handler=log_handler)

                bs_type, stock_code, price = is_match.groups()
                logger.info(f"{bs_type} {stock_code} {price}")
                price = float(price)
                print(bs_type, stock_code, price)
                if bs_type == '买入':
                    if not livelib.in_entrust(m, stock_code):
                    # if True:
                        vol, price = livelib.get_vol_price(m, wt, price)
                        if vol == 0:
                            return 
                        logger.info(f"买入 {stock_code} at {price} {vol}")
                        m.user.buy(stock_code, price, vol)
                elif bs_type == '卖出':
                    p = livelib.get_position(m, stock_code)
                    if p is None:
                        return 
                    if p.enable_amount == 0:
                        logger.info(f"不可卖出（今日买入/已委托）")
                        return 
                    logger.info(f"卖出 {stock_code} at {price} 全部股份")
                    m.user.sell(stock_code, price, p.enable_amount)

# s = "asd9012xzmc 卖出603201成交价格28.46元"        

# m = re.match(pattern_order, s)
# if m:
#     print(m.groups())
# 多线程HTTP服务器
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

# 指定服务器的地址和端口
server_address = ('', 8000)

# 创建多线程HTTP服务器实例并指定处理请求的类
# httpd = ThreadedHTTPServer(server_address, RequestHandler)

# 启动服务器
# print('Server started on port 8000...')
# httpd_thread = threading.Thread(target=httpd.serve_forever)
# httpd_thread.start()

print('Server started on port 8000...')
httpd = HTTPServer(server_address, RequestHandler)
httpd.serve_forever()


