import time
from keys import api_key, secret_key
import requests
import hmac
import hashlib

class Bybit:
    symbol = 'DOGSUSDT'
    limit = 5
    decimals = 6
    usdt_to_trade = 110
    qty_decimals = 1
    price_boost = 0.025

    token_bought = 0
    sleep_time = 0.1
    base_endpoint = 'https://api.bybit.com/v5'
    base_endpoint = 'https://api-demo.bybit.com/v5'
    orderbook_endpoint = '/market/orderbook?'

    def hashing(self, query_string):
        return hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    def get_proxy(self):
        with open("proxys.txt") as my_file:
            line = my_file.read()
            mas = line.split(':')
            proxy_ip = mas[0]
            proxy_port = mas[1]
            proxy_login = mas[2]
            proxy_password = mas[3]

        proxies = {
            # 'https': 'http://proxy_ip:proxy_port'
            'https': f'http://{proxy_login}:{proxy_password}@{proxy_ip}:{proxy_port}'
        }

        return proxies

    def get_decimals(self, number):
        decimal_part = str(number).split('.')[1]
        digits_after_decimal = len(decimal_part)

        return digits_after_decimal

    def get_orderbook(self) -> dict:
        cat = 'spot'
        url = Bybit.base_endpoint + Bybit.orderbook_endpoint + f'symbol={self.symbol}&category={cat}&limit={self.limit}'
        response = requests.get(url=url, proxies=self.get_proxy())

        with open(r'logs\orderbook.txt', 'a') as file:
            file.write(response.text + str('\n'))

        return response.json()['result']

    def get_average_price(self, array):
        total_usdt = 0
        total_token = 0

        self.decimals = self.get_decimals(array[0][0])
        print(f'decimals = {self.decimals}')

        for i in array:
            token_amount = float(i[1])
            price = float(i[0])
            total_token += token_amount
            total_usdt += token_amount * price

        average_price = total_usdt / total_token

        return average_price

    def fast_buy(self):
        orderbook = self.get_orderbook()
        lowest_sell_prices = orderbook['a']

        average_sell_price = round(self.get_average_price(lowest_sell_prices) * (1 + Bybit.price_boost), self.decimals)
        qty = round(Bybit.usdt_to_trade / average_sell_price, self.qty_decimals)
        print(f'trying to buy {qty} tokens, price {average_sell_price}')
        self.limit_open_order(symbol=self.symbol, side="BUY", orderType="Limit", qty=qty, price=average_sell_price)

        self.token_bought = round(qty * 0.998, self.qty_decimals)
        print(f'bought = {qty} tokens')

    def fast_sell(self):
        orderbook = self.get_orderbook()
        highest_buy_prices = orderbook['b']

        average_buy_price = round(self.get_average_price(highest_buy_prices) * (1 - Bybit.price_boost), self.decimals)
        qty = self.token_bought
        print(f'trying to sell {qty} tokens, price = {average_buy_price}')
        self.limit_open_order(symbol=self.symbol, side="SELL", orderType="Limit", qty=qty, price=average_buy_price)

    def token_splash(self):
        while True:
            try:
                self.fast_buy()
                self.fast_sell()
                return True
            except Exception as exception:
                print("Не удалось торговать, попробую снова")
                print(exception)

            time.sleep(self.sleep_time)

    def limit_open_order(self, symbol, side, orderType, qty, price, category='spot'):

        url = 'https://api.bybit.com/v5/order/create'
        #url = 'https://api-demo.bybit.com/v5/order/create'
        current_time = int(time.time() * 1000)
        data = '{' + f'"symbol": "{symbol}", "side": "{side}", "orderType": "{orderType}", "qty": "{qty}", "price": "{price}", "category": "{category}"' + '}'
        sign = self.hashing(str(current_time) + api_key + '5000' + data)

        headers = {
            'X-BAPI-API-KEY': api_key,
            'X-BAPI-TIMESTAMP': str(current_time),
            'X-BAPI-SIGN': sign,
            'X-BAPI-RECV-WINDOW': str(5000),
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.138 Safari/537.36'
        }


        response = requests.post(url=url, headers=headers, data=data, proxies=self.get_proxy())
        print(response.status_code)
        print(response.text)
        return response.text



bybit = Bybit()
time1 = time.time()
bybit.token_splash()
time2 = time.time()
print("Time left: " + str(time2-time1))