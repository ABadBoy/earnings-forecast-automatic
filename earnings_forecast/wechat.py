import urllib.request
import urllib.parse
import json

def get_access_token(app_id: str, app_secret: str) -> str:
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
        if 'access_token' in data:
            return data['access_token']
        else:
            raise Exception(f"Failed to get access token: {data}")

def add_draft(access_token: str, title: str, content: str, thumb_media_id: str) -> str:
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    payload = {
        "articles": [
            {
                "title": title,
                "content": content,
                "thumb_media_id": thumb_media_id
            }
        ]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        if 'media_id' in data:
            return data['media_id']
        else:
            raise Exception(f"Failed to add draft: {data}")
