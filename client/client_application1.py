# coding:utf-8
from clientstub import *
from client_function import *

"""
说明：
    本文件与clientapplication2.py和clientapplication3.py都为客户端应用，只在测试函数的参数上有微调。
    客户端应用创建存根实例后，即可通过存根直接以本地调用函数的方式调用远程服务，
    应用使用简单，除了注册中心的地址外无需其他配置
依赖文件：
    客户端存根在clientstub.py中，
    此外还有一个获取命令行参数的方法在client_function.py中
运行说明：
    必须提供注册中心的ip和端口号才能运行，输入格式如下：
        python clientapplication1.py -i [ip] -p [port]
    其中，ip格式支持ipv4和ipv6
    如需更多说明，可输入：
        python clientapplication1.py -h    
"""

if __name__ == '__main__':
    # 处理命令行参数，获取注册中心的ip和端口号
    # center_ip, center_port = get_args(sys.argv[1:]) # todo
    # center_port = int(center_port)
    center_ip = '127.0.0.1'  # 127.0.0.1 or 192.168.1.20
    center_port = 12000
    # 测试次数（每轮测试都会新建新的存根，并向注册中心申请服务）
    test_time = 20000
    for _ in range(test_time):
        # 创建客户端
        client = ClientStub(center_ip, center_port)
        # 以本地调用的形式，调用远程服务
        add_test = client.my_add(1, 2)
        sub_test = client.my_sub(1, 2)
        mul_test = client.my_mul(1, 2)
        div_test = client.my_div(1, 2)
        pow_test = client.my_pow(1, 2)
        abs_test = client.my_abs(-1)
        sqrt_test = client.my_sqrt(4)
        upper_test = client.my_upper('hello')
        lower_test = client.my_lower('HELLO')
        cat_test = client.my_cat('hello', 'world')
        spilt_test = client.my_split('hello world', ' ')
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
