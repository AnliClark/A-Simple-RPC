from clientstub import *

if __name__ == '__main__':
    # 处理命令行参数
    # ip, port = get_args(sys.argv[1:]) # todo
    center_ip = '127.0.0.1'
    center_port = 12000
    # 创建客户端
    client = ClientStub(center_ip, center_port)
    # 调用远程服务
    add_test = client.call_service('add', (1, 2))
    print(add_test)
    # 关闭客户端
    client.close()