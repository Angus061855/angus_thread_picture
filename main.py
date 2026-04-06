import os
import requests
import cloudinary
import cloudinary.uploader
from generate_image import generate_image
from generate_caption import generate_caption

# ===== 環境變數 =====
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Cloudinary 設定
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


def get_pending_posts():
    """從 Notion 取得狀態為「待發」的文章"""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "狀態",
            "status": {"equals": "待發"}
        },
        "page_size": 1
    }
    res = requests.post(url, headers=NOTION_HEADERS, json=payload)
    data = res.json()
    return data.get("results", [])


def get_text_from_page(page):
    """從 Notion page 取得「文字」欄位"""
    text_prop = page["properties"].get("文字", {})
    rich_texts = text_prop.get("rich_text", [])
    return "".join([rt["plain_text"] for rt in rich_texts])


def get_topic_from_page(page):
    """從 Notion page 取得「主題」欄位"""
    topic_prop = page["properties"].get("主題", {})
    rich_texts = topic_prop.get("rich_text", [])
    return "".join([rt["plain_text"] for rt in rich_texts])


def upload_to_cloudinary(image_path):
    """上傳圖片到 Cloudinary"""
    result = cloudinary.uploader.upload(image_path)
    return result["secure_url"]


def update_notion_page(page_id, image_url, caption):
    """更新 Notion 頁面：圖片網址、文案、狀態"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "圖片網址": {
                "url": image_url
            },
            "文案": {
                "rich_text": [{"text": {"content": caption[:2000]}}]
            },
            "狀態": {
                "status": {"name": "待發"}
            }
        }
    }
    requests.patch(url, headers=NOTION_HEADERS, json=payload)


def post_to_instagram(image_url, caption):
    """發布到 Instagram"""
    # Step 1: 建立媒體容器
    create_url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
    create_payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }
    res = requests.post(create_url, data=create_payload)
    creation_id = res.json().get("id")

    if not creation_id:
        print(f"IG 建立媒體失敗：{res.json()}")
        return False

    # Step 2: 發布
    publish_url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN
    }
    pub_res = requests.post(publish_url, data=publish_payload)
    print(f"IG 發布結果：{pub_res.json()}")
    return pub_res.json().get("id") is not None


def update_status_published(page_id):
    """更新 Notion 狀態為已發布"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "狀態": {"status": {"name": "已發布"}}
        }
    }
    requests.patch(url, headers=NOTION_HEADERS, json=payload)


def send_telegram_notification(message):
    """發送 Telegram 通知"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)


def main():
    posts = get_pending_posts()
    if not posts:
        print("沒有待發文章")
        return

    page = posts[0]
    page_id = page["id"]
    text = get_text_from_page(page)

    if not text:
        print("文字欄位為空，跳過")
        return

    print(f"處理文章：{text[:30]}...")

    # Step 1: 生成圖片
    image_path = generate_image(text, "output.png")

    # Step 2: 上傳 Cloudinary
    image_url = upload_to_cloudinary(image_path)
    print(f"圖片上傳成功：{image_url}")

    # Step 3: 生成文案
    caption = generate_caption(text)
    print(f"文案生成完成：{caption[:50]}...")

    # Step 4: 更新 Notion（圖片網址 + 文案）
    update_notion_page(page_id, image_url, caption)

    # Step 5: 發布 IG
    success = post_to_instagram(image_url, caption)

    if success:
        update_status_published(page_id)
        send_telegram_notification(f"✅ IG 發布成功！\n\n{text[:50]}...")
        print("發布成功！")
    else:
        send_telegram_notification(f"❌ IG 發布失敗\n\n{text[:50]}...")
        print("發布失敗")


if __name__ == "__main__":
    main()
