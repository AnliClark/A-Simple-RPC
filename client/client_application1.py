from clientstub import *

if __name__ == '__main__':
    # 处理命令行参数
    # ip, port = get_args(sys.argv[1:]) # todo
    # center_port = int(center_port)
    center_ip = '192.168.1.20'  # 127.0.0.1 or 192.168.1.20 todo
    center_port = 12000
    # 创建客户端
    client = ClientStub(center_ip, center_port)
    # 以本地调用的形式，调用远程服务
    add_test = client.add(1, 2)
    sub_test = client.sub(1, 2)
    mul_test = client.mul(1, 2)
    div_test = client.div(1, 2)
    print(add_test)
    print(sub_test)
    print(mul_test)
    print(div_test)
    # 关闭客户端
    client.close()