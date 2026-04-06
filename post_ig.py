import os
import requests
from notion_client import Client

# 初始化
notion = Client(auth=os.environ["NOTION_TOKEN"])
DATABASE_ID = "33a11a316c9e80b793f3eeb04850b385"

IG_USER_ID = os.environ["IG_USER_ID"]
IG_ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }, timeout=15)
    except Exception as e:
        print(f"Telegram 通知失敗：{e}")

def get_pending_pages():
    response = notion.databases.query(
        **{
            "database_id": DATABASE_ID,
            "filter": {
                "property": "狀態",
                "status": {"equals": "待發"}
            },
            "page_size": 1
        }
    )
    return response["results"]

def post_to_instagram(image_url, caption):
    # Step 1：建立媒體容器
    container_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
    container_res = requests.post(container_url, data={
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }, timeout=30)
    container_data = container_res.json()
    print(f"容器回應：{container_data}")

    if "id" not in container_data:
        raise Exception(f"建立容器失敗：{container_data}")

    creation_id = container_data["id"]

    # Step 2：發布
    publish_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
    publish_res = requests.post(publish_url, data={
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN
    }, timeout=30)
    publish_data = publish_res.json()
    print(f"發布回應：{publish_data}")

    if "id" not in publish_data:
        raise Exception(f"發布失敗：{publish_data}")

    return publish_data["id"]

def update_notion_status(page_id):
    notion.pages.update(
        page_id=page_id,
        properties={
            "狀態": {
                "status": {"name": "已發布"}
            }
        }
    )

def main():
    pages = get_pending_pages()
    print(f"找到 {len(pages)} 筆待發文章")

    if not pages:
        print("沒有待發文章")
        send_telegram("ℹ️ 帳號A：今天沒有待發文章")
        return

    page = pages[0]  # 一次只發一篇
    page_id = page["id"]
    props = page["properties"]

    # 取得圖片網址
    image_url = props.get("圖片網址", {}).get("url", "")

    # 取得文案
    rich_text = props.get("文案", {}).get("rich_text", [])
    caption = rich_text[0]["plain_text"] if rich_text else ""

    print(f"圖片網址：{image_url}")
    print(f"文案長度：{len(caption)} 字")

    if not image_url:
        msg = f"❌ 帳號A IG發文失敗：圖片網址為空（{page_id}）"
        print(msg)
        send_telegram(msg)
        return

    if not caption:
        msg = f"❌ 帳號A IG發文失敗：文案為空（{page_id}）"
        print(msg)
        send_telegram(msg)
        return

    try:
        post_id = post_to_instagram(image_url, caption)
        update_notion_status(page_id)
        msg = f"✅ 帳號A IG已發\n貼文ID：{post_id}"
        print(msg)
        send_telegram(msg)
    except Exception as e:
        msg = f"❌ 帳號A IG發文失敗：{str(e)}"
        print(msg)
        send_telegram(msg)

if __name__ == "__main__":
    main()
