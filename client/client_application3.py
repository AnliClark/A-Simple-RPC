# coding:utf-8
from clientstub import *
from client_function import *

"""
说明：
    本文件与clientapplication1.py和clientapplication2.py都为客户端应用，只在测试函数的参数上有微调。
    详细说明可见clientapplication1.py
"""

if __name__ == '__main__':
    # 处理命令行参数，获取注册中心的ip和端口号
    center_ip, center_port = get_args(sys.argv[1:])
    center_port = int(center_port)
    # 测试次数（每轮测试都会新建新的存根，并向注册中心申请服务）
    test_time = 1000
    for _ in range(test_time):
        # 创建客户端
        client = ClientStub(center_ip, center_port)
        # 以本地调用的形式，调用远程服务
        add_test = client.my_add(9, 5)
        sub_test = client.my_sub(9, 5)
        mul_test = client.my_mul(9, 5)
        div_test = client.my_div(9, 5)
        pow_test = client.my_pow(9, 3)
        abs_test = client.my_abs(3)
        sqrt_test = client.my_sqrt(7)
        upper_test = client.my_upper('hello world from rpc')
        lower_test = client.my_lower('HELLO WORLD FROM RPC')
        cat_test = client.my_cat('hello world', 'from rpc')
        spilt_test = client.my_split('W1W2W3W4', 'W')
        print(add_test)
        print(sub_test)
        print(mul_test)
        print(div_test)
        print(pow_test)
        print(abs_test)
        print(sqrt_test)
        print(upper_test)
        print(lower_test)
        print(cat_test)
        print(spilt_test)

    print(f'{test_time}次测试结束')
