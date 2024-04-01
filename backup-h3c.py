import logging
import telnetlib
import time
import datetime
from multiprocessing import Pool
from threading import Thread

class TelnetClient():
    def __init__(self,):
        self.tn = telnetlib.Telnet()

    # 此函数实现telnet登录主机
    def login_host(self,host_ip,username,password):
        try:
            # self.tn = telnetlib.Telnet(host_ip,port=23)
            self.tn.open(host_ip,port=23)
        except:
            logging.warning('%s网络连接失败'%host_ip)
            return False
        # 等待login出现后输入用户名，最多等待10秒
        self.tn.read_until(b'Login: ',timeout=10)
        self.tn.write(username.encode()+b'\n')

        # 等待Password出现后输入用户名，最多等待10秒
        self.tn.read_until(b'Password: ',timeout=10)
        self.tn.write(password.encode()+b'\n')
        # 延时两秒再收取返回结果，给服务端足够响应时间
        time.sleep(2)
        # 获取登录结果
        # read_very_eager()获取到的是的是上次获取之后本次获取之前的所有输出
        command_result = self.tn.read_very_eager()
        if 'Login failed'.encode('ascii') not in command_result and 'authentication failed'.encode('ascii') not in command_result:
            logging.warning('登录成功:{}'.format(host_ip))
            return self.tn
        else:
            logging.warning('登录失败，用户名或密码错误:{}'.format(host_ip))
            return False

    # 此函数实现执行传过来的命令，并输出其执行结果
    def execute_some_command(self,tn,command):
        # 执行命令
        print(command)
        time.sleep(2)
        tn.write(command.encode('ascii')+b'\n')
        # 获取命令结果
        time.sleep(5)
        command_result = tn.read_very_eager()
        # command_result=self.tn.read_all().decode('ascii')
        logging.warning('命令执行结果:{}'.format(command_result))

    # 退出telnet
    def logout_host(self,tn):
        tn.write(b"quit"+b'\n')

#执行交换机备份
def switchbak(i,u,p,c):
    telnet_client = TelnetClient()
    tn = telnet_client.login_host(i,u,p)

    if  tn:
        telnet_client.execute_some_command(tn,c)
        time.sleep(2)
        telnet_client.logout_host(tn)


if __name__ == '__main__':
    print('开始多进程并发备份')
    start=time.time()
    p=Pool(50)
    #50为进程数，用户可根据客户端及服务器配置自行调整，注意：过大进程易被安全软件识别为恶意攻击
    for ip in open('switchs.txt').readlines():
        ip=ip.strip()
        #交换机具备backup命令的telnet用户
        username = 'admin'
        #该用户密码
        password = 'xxx'
        #tftp服务器地址
        #ftphost ='172.15.131.117'
        ftphost = '172.15.108.32'
        filename = ip.replace('.','.')+ '-'+datetime.date.today().strftime('%Y%m%d')+'.cfg'
        command1 = 'backup startup-configuration to ' +(ftphost)+' '+ filename
        p.apply_async(switchbak,args=(ip,username,password,command1))
    p.close()
    p.join()
    end=time.time()
    print('备份完成，耗时：%0.2f 秒' %(end-start))