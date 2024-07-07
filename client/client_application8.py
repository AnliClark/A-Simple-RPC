from clientstub import *
from client_function import *

if __name__ == '__main__':
    # 处理命令行参数
    center_ip, center_port = get_args(sys.argv[1:])
    center_port = int(center_port)
    for _ in range(20):
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
        # 关闭客户端
        client.close()
