
[TOC]
## 插件功能
1. 发送企业微信消息(需要配置ESB)
2. 发送邮件消息(需要配置ESB)
3. 发送群消息
   
## 插件打包
 1. 进入插件代码工程根目录下
 2. 执行 python setup.py sdist (或其他打包命令，本示例以sdist为例)
 3. 在任意位置新建文件夹，如 sendmsg_release
 4. 将步骤 2 生产的执行包拷贝到 sendmsg_release 下
 5. 添加task.json文件到 sendmsg_release 下
 6. 把 sendmsg_release 使用`zip -r sendmsg.zip sendmsg_release`打成zip包即可 

## 安装插件
1. 插件名称随便取
2. 插件标识必须为sendmsg
3. 开发语言为python
4. 自定义前端选否
5. 适用机器类型选择编译环境（Linux + Windows + MacOS）
   
## 私有配置
1. bk_app_code: 蓝盾app code
2. bk_app_secret: 蓝盾app secret
3. bk_host: paas地址
4. bk_username: 调用ESB接口的用户，可为admin
5. robot_webhook: 企业微信机器人webhook地址（不包含key), 为`https://qyapi.weixin.qq.com/cgi-bin/webhook/send`
6. usermgr_host: http://{usermgr_ip}:8009, usermgr_ip为部署用户管理服务的机器IP

```
source ${CTRL_DIR:-/data/install}/load_env.sh

echo "bk_app_code      $BK_CI_APP_CODE"
echo "bk_app_secret    $BK_CI_APP_TOKEN"
echo "bk_host          $BK_PAAS_PUBLIC_URL"
echo "usermgr_host     http://${BK_USERMGR_IP}:8009"


# 参考输出
bk_app_code       bk_ci
bk_app_secret     略
bk_host           http://paas.bktencent.com:80
usermgr_host      http://192.168.1.1:8009
```

## 企业微信配置

### 配置用于蓝鲸消息通知的应用

需要以管理员身份创建一个应用，或者选择已有的应用，类似于应用号，企业微信消息会从该应用发送消息给用户，配置方法

登录[企业微信Web端](https://work.weixin.qq.com/wework_admin/frame#apps)- 「应用管理」，将应用的可见范围设置为全企业人员（或至少设置为可能需要接送微信消息通知的人员）


### 获取应用信息

需要获取一下信息：

1. "企业微信web端 → 我的企业 → 企业信息" 获取CorpID
2. “企业微信web端 → 应用管理 → 选择对应应用” 获取应用Secret
> 比如选择上述步骤创建的应用，查看应用详情，点击「查看」，应用的secret会发送到企业微信上
3. “企业微信web端 → 应用管理 → 选择对应应用” 获取AgentId
> 应用详情页面可以获取agentid

### 配置Web网页登录授权回调域

"企业微信Web端 → 应用管理 → 选择对应的应用 → 企业微信授权登录 → 设置 → Web网页 → 设置授权回调域"， 设置蓝鲸paas域名（比如paas.bktencent.com）为登录授权回调域 （非80端口则paas.bktencent.com需带上端口）

### ESB配置

「开发者中心」-「API网关」-「通道管理」-「搜索cmsi」-「选择发送微信消息」

1. wx_type选择「企业微信」
2. wx_qy_corpid填写Corpid
3. wx_qy_corpsecret填写Secret
4. wx_qy_agentid填写Agentid

### 绑定企业微信

要发送企业微信消息，需要用户绑定企业微信号，有两种绑定方式：

1. 「个人中心」-「绑定微信」，然后打开手机企业微信扫码
2. 「用户管理」-「编辑个人信息」-「微信」，然后填写个人企业微信账号

### 选择消息发送方式

在蓝盾里使用本插件（需要选择编译环境）, 选择发送企业微信方式，发送目标为蓝鲸用户名

## 自定义变量使用
目前支持的自定义变量有
```
BK_CI_START_FULLNAME  表示流水线启动者的全名
```
使用方式：在插件标题或者内容里`${BK_CI_START_FULLNAME}`引用即可


