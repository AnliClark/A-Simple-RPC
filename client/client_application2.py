# coding:utf-8
from clientstub import *
from client_function import *

"""
说明：
    本文件与clientapplication1.py和clientapplication3.py都为客户端应用，只在测试函数的参数上有微调。
    详细说明可见clientapplication1.py
"""

if __name__ == '__main__':
    # 处理命令行参数，获取注册中心的ip和端口号
    center_ip, center_port = get_args(sys.argv[1:])
    center_port = int(center_port)
    # 测试次数（每轮测试都会新建新的存根，并向注册中心申请服务）
    test_time = 100
    for _ in range(test_time):
        # 创建客户端
        client = ClientStub(center_ip, center_port)
        # 以本地调用的形式，调用远程服务
        add_test = client.my_add(4, 5)
        sub_test = client.my_sub(4, 5)
        mul_test = client.my_mul(4, 5)
        div_test = client.my_div(4, 5)
        pow_test = client.my_pow(4, 5)
        abs_test = client.my_abs(-4)
        sqrt_test = client.my_sqrt(5)
        upper_test = client.my_upper('hello world')
        lower_test = client.my_lower('HELLO WORLD')
        cat_test = client.my_cat('hello world', 'python')
        spilt_test = client.my_split('hello world python', ' ')
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
        time.sleep(0.3)

    print(f'{test_time}次测试结束')
