import json

import lark_oapi as lark
from lark_oapi.api.im.v1 import *

# SDK 使用说明: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/server-side-sdk/python--sdk/preparations-before-development

client = lark.Client.builder() \
        .app_id("cli_a816fd580ab7500c") \
        .app_secret("mRVPxE6b85gkWzlXiRI6ah0iJYcSyh0X") \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

chat_id = 'oc_12c2dcf90ce96bed5b99ea2688720468' # 太平洋钓鱼群
user_id = '6ad1g3c4' # gzw user id  
        
def send_normal_msg_to_group(title, content):
    payload = json.dumps({
                "text": f"{title}\n{content}"
    })
    request: CreateMessageRequest = CreateMessageRequest.builder() \
        .receive_id_type("chat_id") \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id(chat_id)
            .msg_type("text") # 卡片消息
            .content(payload)
            .build()) \
        .build()
        
    response: CreateMessageResponse = client.im.v1.message.create(request)
    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
        return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return response

def send_buy_stock_msg_to_group(strategy_name, stock_code, price):
    content = json.dumps({
        "type": "template",
        "data": {
            "template_id": "AAqzXKrGvfcPj",
            "template_version_name": "1.0.2",
            "template_variable": {
                "color": "green",
                "price": price,          # 直接引用变量
                "operate_type": "买入",
                "stock_codes": stock_code,
                "strategy_name": strategy_name
            }
        }
    }, ensure_ascii=False)
    
    request: CreateMessageRequest = CreateMessageRequest.builder() \
        .receive_id_type("chat_id") \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id(chat_id)
            .msg_type("interactive") # 卡片消息
            .content(content)
            .build()) \
        .build()
        
    response: CreateMessageResponse = client.im.v1.message.create(request)
    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
        return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return response

    

def send_sell_stock_msg_to_group(strategy_name, stock_code, price):
    content = json.dumps({
        "type": "template",
        "data": {
            "template_id": "AAqzXKrGvfcPj",
            "template_version_name": "1.0.2",
            "template_variable": {
                "color": "red",
                "price": price,          # 直接引用变量
                "operate_type": "卖出",
                "stock_codes": stock_code,
                "strategy_name": strategy_name
            }
        }
    }, ensure_ascii=False)
    
    request: CreateMessageRequest = CreateMessageRequest.builder() \
        .receive_id_type("chat_id") \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id(chat_id)
            .msg_type("interactive") # 卡片消息
            .content(content)
            .build()) \
        .build()
        
    response: CreateMessageResponse = client.im.v1.message.create(request)
        # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
        return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return response
