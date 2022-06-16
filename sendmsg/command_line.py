# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import json
import os
import base64
import sys
from string import Template

import requests

import python_atom_sdk as sdk
from .error_code import ErrorCode

err_code = ErrorCode()


def exit_with_error(error_type=None, error_code=None, error_msg="failed"):
    """
    @summary: exit with error
    """
    if not error_type:
        error_type = sdk.OutputErrorType.PLUGIN
    if not error_code:
        error_code = err_code.PLUGIN_ERROR
    sdk.log.error("error_type: {}, error_code: {}, error_msg: {}".format(error_type, error_code, error_msg))

    output_data = {
        "status":    sdk.status.FAILURE,
        "errorType": error_type,
        "errorCode": error_code,
        "message":   error_msg,
        "type":      sdk.output_template_type.DEFAULT
    }
    sdk.set_output(output_data)

    exit(error_code)


def exit_with_succ(data=None, quality_data=None, msg="run succ"):
    """
    @summary: exit with succ
    """
    if not data:
        data = {}

    output_template = sdk.output_template_type.DEFAULT
    if quality_data:
        output_template = sdk.output_template_type.QUALITY

    output_data = {
        "status":  sdk.status.SUCCESS,
        "message": msg,
        "type":    output_template,
        "data":    data
    }

    if quality_data:
        output_data["qualityData"] = quality_data

    sdk.set_output(output_data)

    sdk.log.info("finish")
    exit(err_code.OK)


def get_kwargs_map():
    """
    @summary: self-defined variable map based on BK
    """
    kwargs_map = {}
    usermgr_host = sdk.get_sensitive_conf("usermgr_host")
    if usermgr_host:
        username = sdk.get_pipeline_start_user_name()
        api_url = usermgr_host + "/api/v2/profiles/{}/?lookup_field=username".format(username)
        resp = requests.get(api_url)
        resp_j = resp.json()
        if resp_j["code"] != 0:
            sdk.log.info("request %s failed, please connact the devloper."%api_url)
            return kwargs_map
        display_name = resp_j["data"]["display_name"]
        kwargs_map["BK_CI_START_FULLNAME"] = display_name
    else:
        sdk.log.info("wrong config, please check sensitive config.")
        return kwargs_map
    return kwargs_map
    
def get_response(url, method, data=None, desc=""):
    if method == "get":
        resp = requests.get(url)
    elif method == "post":
        headers = {"Content-Type": "application/json; charset=utf-8"}
        sdk.log.info("%s send data: %s"%(desc, data))
        resp = requests.post(url, headers=headers, data=json.dumps(data))
    else:
        exit_with_error(
            error_type=sdk.output_error_type.USER,
            error_code=err_code.USER_CONFIG_ERROR,
            error_msg="method is not get or post."
        )
    if resp.status_code != 200:
        exit_with_error(error_type=sdk.output_error_type.THIRD_PARTY,
                        error_code=err_code.THIRD_PARTY,
                        error_msg=resp.text)
    resp_json = resp.json()
    
    sdk.log.info("{} response data is {}".format(desc, resp_json))
    if resp_json["code"] != 0:
        exit_with_error(error_type=sdk.output_error_type.USER,
                        error_code=err_code.USER_CONFIG_ERROR,
                        error_msg=resp_json["message"])
    return resp_json

def main():
    """
    @summary: main
    """
    sdk.log.info("enter main")
    
    # 插件私有配置
    bk_app_code = sdk.get_sensitive_conf("bk_app_code")
    bk_app_secret = sdk.get_sensitive_conf("bk_app_secret")
    bk_host = sdk.get_sensitive_conf("bk_host")
    bk_username = sdk.get_sensitive_conf("bk_username")
    
    if bk_app_code is None:
        exit_with_error(
            error_type=sdk.output_error_type.USER,
            error_code=err_code.USER_CONFIG_ERROR,
            error_msg="bk_app_code cannot be empty"
        )
    
    if bk_app_secret is None:
        exit_with_error(
            error_type=sdk.output_error_type.USER,
            error_code=err_code.USER_CONFIG_ERROR,
            error_msg="bk_app_secret cannot be empty"
        )
    
    if bk_host is None:
        exit_with_error(
            error_type=sdk.output_error_type.USER,
            error_code=err_code.USER_CONFIG_ERROR,
            error_msg="bk_host cannot be empty"
        )
    bk_host = bk_host.rstrip("/")

    if bk_username is None:
        exit_with_error(
            error_type=sdk.output_error_type.USER,
            error_code=err_code.USER_CONFIG_ERROR,
            error_msg="bk_username cannot be empty"
        )

    # 输入
    input_params = sdk.get_input()
    kwargs_map = get_kwargs_map()

    # 企业微信/钉钉接收人
    send_by = []
    send_to = ""
    send_by_str = input_params.get("send_by", None)
    if send_by_str:
        send_by = json.loads(send_by_str)
        sdk.log.info("send_by is {}".format(send_by))
        if "mail" in send_by or "dingtalk" in send_by or "weixin" in send_by:

            send_to = input_params.get("send_to", None)
            send_to = json.loads(send_to)
            send_to = ",".join(send_to)



    # 邮件接收人
    mail_receiver = input_params.get("mail_receiver")
    mail_list = ""
    if "mail" in send_by and mail_receiver:
        receivers = json.loads(mail_receiver)

        # 获取非完整邮箱地址
        usernames = list(filter(lambda x: "@" not in x, receivers))
        sdk.log.info("receiver usernames is {}".format(usernames))
        # 完整邮箱地址
        mails = list(filter(lambda x: "@" in x, receivers))

        list_user_url = bk_host + "/api/c/compapi/v2/usermanage/list_users/"
        request_data = {
            "bk_app_code": bk_app_code,
            "bk_app_secret": bk_app_secret,
            "bk_username": bk_username,
            "fields": "username,email",
            "exact_lookups": ",".join(usernames)
        }
        resp_json = get_response(url=list_user_url, method="post", data=request_data, desc="list_users")

        for item in resp_json["data"]["results"]:
            # 判断获取到的邮箱地址是否已经存在
            if item["email"] not in mails: 
                mails.append(item["email"])
        mail_list = ",".join(mails)
        sdk.log.info("email receiver is {}".format(mail_list))

    # 企业微信/钉钉/邮件的共同发送内容
    title = ""
    content = ""
    if send_to or mail_receiver:

        title = input_params.get("title", None)
        title_tpl = Template(title)
        title = title_tpl.safe_substitute(kwargs_map)
        sdk.log.info("title is {}".format(title))

        content = input_params.get("content", None)
        content_tpl = Template(content)
        content = content_tpl.safe_substitute(kwargs_map)
        sdk.log.info("content is {}".format(content))

    # 企业微信机器人配置
    send_by_webot_str = input_params.get("send_by_webot", None)
    sdk.log.info("send_by_webot is {}".format(send_by_webot_str))
    send_by_webot = False
    webot_key = ""
    webot_msgtype = "text"
    webot_mentioned_list = []
    webot_content = ""
    if send_by_webot_str == "true":
        send_by_webot = True
        webot_key = input_params.get("webot_key", None)
        if not webot_key:
            exit_with_error(
                error_type=sdk.output_error_type.USER,
                error_code=err_code.USER_CONFIG_ERROR,
                error_msg="webot_key is None"
            )
        sdk.log.info("webot_key is {}".format(webot_key))
        
        webot_msgtype = input_params.get("webot_msgtype", None)
        sdk.log.info("webot_msgtype is {}".format(webot_msgtype))
        
        if webot_msgtype == "text":
            webot_mentioned = input_params.get("webot_mentioned", None)
            if webot_mentioned:
                webot_mentioned_list = json.loads(webot_mentioned)
            sdk.log.info("webot_mentioned_list is {}".format(webot_mentioned_list))

        webot_content = input_params.get("webot_content", None)
        webot_content_tpl = Template(webot_content)
        webot_content = webot_content_tpl.safe_substitute(kwargs_map)
        sdk.log.info("robot_content is {}".format(webot_content))

    # 钉钉机器人配置
    send_by_dingbot_str = input_params.get("send_by_dingbot", None)
    send_by_dingbot = False
    dingbot_receiver = ""
    dingbot_content = ""
    if send_by_dingbot_str == "true":
        send_by_dingbot = True
        dingbot_msgtype = input_params.get("dingbot_msgtype", None)
        if not dingbot_msgtype:
            exit_with_error(
                error_type=sdk.output_error_type.USER,
                error_code=err_code.USER_CONFIG_ERROR,
                error_msg="dingbot_msgtype is None"
            )
        sdk.log.info("dingbot_msgtype is {}".format(dingbot_msgtype))

        dingbot_receiver = json.loads(input_params.get("dingbot_receiver"))
        dingbot_receiver = ",".join(dingbot_receiver)
        dingbot_at_username_list = []
        dingbot_at_mobile_list = []
        ## TODO: 群@功能
        if dingbot_msgtype == "text":
            dingbot_at_username = input_params.get("dingbot_at_username", None)
            if dingbot_at_username:
                dingbot_at_username_list = json.loads(dingbot_at_username)
            dingbot_at_mobile = input_params.get("dingbot_at_mobile", None)
            if dingbot_at_mobile:
                dingbot_at_mobile_list = json.loads(dingbot_at_mobile)
            sdk.log.info("dingbot_at_username_list is {}".format(dingbot_at_username_list))
            sdk.log.info("dingbot_at_mobile_list is {}".format(dingbot_at_mobile_list))
        dingbot_content = input_params.get("dingbot_content", None)
        dingbot_content_tpl = Template(dingbot_content)
        dingbot_content = dingbot_content_tpl.safe_substitute(kwargs_map)
        sdk.log.info("dingbot_content is {}".format(dingbot_content))



    # 消息发送逻辑

    headers = {"Content-Type": "application/json; charset=utf-8"}
    # 企业微信、钉钉采用send_msg接口发送
    msg_url = bk_host + "/api/c/compapi/cmsi/send_msg/"
    msg_tpl = {
            "bk_app_code": bk_app_code,
            "bk_app_secret": bk_app_secret,
            "bk_username": bk_username,
            "msg_type": "weixin",
            "receiver__username": send_to,
            "title": title,
            "content": content,
        }

    
    sdk.log.info("send_by is {}".format(send_by))
    if "weixin" in send_by:
        msg_tpl["msg_type"] = "weixin"
        sdk.log.info("【weixin】 send data is {}".format(msg_tpl))
        resp_json = get_response(url=msg_url, method="post", data=msg_tpl, desc="weixin")
    
    # 邮件发送逻辑，采用send_mail接口
    if "mail" in send_by:
        mail_url = bk_host + "/api/c/compapi/cmsi/send_mail/"
        mail_data_tpl = {
                "bk_app_code": bk_app_code,
                "bk_app_secret": bk_app_secret,
                "bk_username": bk_username,
                "receiver": mail_list,
                "title": title,
                "content": content,
                "body_format": "Text"
            }
        attachment_file = input_params.get("attachment", None)
        if attachment_file:
            sdk.log.info("attachment is {}".format(attachment_file))
            file_path = os.path.join(sdk.get_workspace(), attachment_file)
            if not os.path.exists(file_path):
                sdk.log.error("{} does not exist in workspace!".format(attachment_file))
            else:
                attachments = []
                with open(file_path, 'rb') as f:
                    content_encoded = base64.b64encode(f.read())
                    if sys.version_info.major == 3:
                        content_encoded = content_encoded.decode('utf-8')
                    item = {
                        "filename": attachment_file,
                        "content": content_encoded
                    }
                    attachments.append(item)
                mail_data_tpl.update({"attachments": attachments})

        resp_json = get_response(url=mail_url, method="post", data=mail_data_tpl, desc="mail")
 
    if "dingtalk" in send_by:
        msg_tpl["msg_type"] = "ding"
        resp_json = get_response(url=msg_url, method="post", data=msg_tpl, desc="dingtalk")


    # 企业微信机器人发送逻辑
    if send_by_webot:
        robot_webhook = sdk.get_sensitive_conf("robot_webhook")
        if robot_webhook is None:
            exit_with_error(
                error_type=sdk.output_error_type.USER,
                error_code=err_code.USER_CONFIG_ERROR,
                error_msg="robot_webhook does not set"
            )
        webhook_url = robot_webhook + "?key=" + webot_key
        sdk.log.info("webhook_url is {}".format(webhook_url))

        artifact = input_params.get("webot_artifact", None)
        if artifact:
            sdk.log.info("artifact is {}".format(artifact))
            file_path = os.path.join(sdk.get_workspace(), artifact)
            sdk.log.info("file_path is {}".format(file_path))
            if not os.path.exists(file_path):
                sdk.log.error("{} does not exist in workspace!".format(artifact))
            else:
                media_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={KEY}&type=file".format(
                    KEY=webot_key
                )
                files = {'file': (artifact, open(file_path, 'rb'), 'text/plain')}
                r = requests.post(url=media_url, files=files)
                r_json = r.json()
                if r.status_code != 200 or r_json["errcode"] != 0:
                    sdk.log.error("failed to upload file, {}".format(r_json["errmsg"]))
                media_id = r_json["media_id"]
                media_body = {
                    "msgtype": "file",
                    "file": {
                        "media_id": media_id
                    }
                }
                r = requests.post(webhook_url, headers=headers, data=json.dumps(media_body))
                r_json = r.json()
                if r.status_code != 200 or r_json["errcode"] != 0:
                    sdk.log.error("failed to send file, {}".format(r_json["errmsg"]))
                sdk.log.info("success to send file {}".format(artifact))

        body = {
            "msgtype": "text",
            "text": {
                "content": "",
                "mentioned_list": webot_mentioned_list
            },
            "markdown": {
                "content": ""
            }
        }
        body["msgtype"] = webot_msgtype
        body[webot_msgtype]["content"] = webot_content
        sdk.log.info("【webot】 send data is is {}".format(body))
        r = requests.post(webhook_url, headers=headers, data=json.dumps(body))
        r_json = r.json()
        if r.status_code != 200 or r_json["errcode"] != 0:
            sdk.log.error("failed to send data, {}".format(r_json["errmsg"]))
        sdk.log.info("success to send data")
    
    # 钉钉机器人发送逻辑
    if send_by_dingbot:
        dingbot_url = bk_host + "/api/c/compapi/cmsi/send_dingbot/"
        dingbot_data_tpl = {
                "bk_app_code": bk_app_code,
                "bk_app_secret": bk_app_secret,
                "bk_username": bk_username,
                "msg_key": "text",
                "receiver__username": dingbot_receiver,
                "content": dingbot_content,
            }
        if dingbot_msgtype == "text":
            dingbot_data_tpl.update({
                "at_username": dingbot_at_username_list,
                "at_mobile": dingbot_at_mobile_list
            })

        elif dingbot_msgtype=="markdown":
            dingbot_data_tpl["msg_key"] = "markdown"
            dingbot_title = input_params.get("dingbot_title")
            title_tpl = Template(dingbot_title)
            dingbot_title = title_tpl.safe_substitute(kwargs_map)
            dingbot_data_tpl.update({"title": dingbot_title})

        resp_json = get_response(url=dingbot_url, method="post", data=dingbot_data_tpl, desc="dingbot")

    # 插件执行结果、输出数据
    if not send_by and not send_by_webot and not send_by_dingbot:
        sdk.log.error("用户没有选择任何的发送方式")
    exit_with_succ()