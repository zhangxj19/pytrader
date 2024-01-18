import requests

# 定义要发送的数据
data = {
    'key1': 'value1',
    'key2': 'value2'
}

# 发送POST请求
response = requests.post('http://192.168.1.7:8000', data=data)

# 处理响应
if response.status_code == 200:
    print('POST request successful')
    print('Response:', response.text)
else:
    print('POST request failed')
    print('Status code:', response.status_code)