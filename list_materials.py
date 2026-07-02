import os
import requests

def get_access_token(app_id: str, app_secret: str) -> str:
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if "access_token" in data:
        return data["access_token"]
    else:
        raise Exception(f"获取 Access Token 失败: {data}")

def list_image_materials(access_token: str):
    # 微信批量获取素材列表接口
    url = f"https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={access_token}"
    
    payload = {
        "type": "image",
        "offset": 0,
        "count": 100  # 获取最新的 20 张图片
    }
    
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    
    if "item" not in data:
        print(f"获取素材失败: {data}")
        return

    items = data["item"]
    if not items:
        print("您的素材库中当前没有图片素材。")
        return
        
    print(f"共找到 {len(items)} 张最新图片素材：\n")
    for item in items:
        print(f"文件名称: {item.get('name')}")
        print(f"Media_ID: {item.get('media_id')}")
        print("-" * 50)

if __name__ == "__main__":
    from earnings_forecast.config import settings
    app_id = settings.wechat_app_id
    app_secret = settings.wechat_app_secret
    
    if not app_id or not app_secret:
        print("错误：缺少 WECHAT_APP_ID 或 WECHAT_APP_SECRET 环境变量。")
        print("请在 earnings_forecast/config.py 中配置或设置环境变量。")
    else:
        print("正在连接微信服务器获取素材库...")
        try:
            token = get_access_token(app_id, app_secret)
            list_image_materials(token)
        except Exception as e:
            print(f"发生错误: {e}")
