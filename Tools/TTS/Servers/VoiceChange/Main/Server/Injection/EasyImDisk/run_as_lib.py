import subprocess
NORMAL_ACCESS = "0x10000"
USER_ACCESS = "0x20000"
ADMIN_ACCESS = "0x40000"
WIN_RUNAS_HEAD = ["runas", "/trustlevel:*******"]
def run(cmdtxt:list,runas_access = ADMIN_ACCESS,join:str = " ",*AdditionInfo,**AdditionParams):
    runas_head = [WIN_RUNAS_HEAD[0],WIN_RUNAS_HEAD[1].replace("*******",str(runas_access))]
    runas_cmd = [*runas_head,f'{join.join(cmdtxt)}']
    return subprocess.Popen(runas_cmd,*AdditionInfo,**AdditionParams)