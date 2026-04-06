import os
import google.generativeai as genai
from notion_client import Client

# 初始化
notion = Client(auth=os.environ["NOTION_API_KEY"])
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

def get_pending_pages():
    """取得狀態為「待發」且文案為空的頁面"""
    response = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "and": [
                {
                    "property": "狀態",
                    "select": {"equals": "待發"}
                },
                {
                    "property": "文案",
                    "rich_text": {"is_empty": True}
                }
            ]
        }
    )
    return response["results"]

def generate_caption(topic):
    """用 Gemini 生成 IG 文案"""
    prompt = f"""
    你是一位專業的 Instagram 文案寫手。
    請根據主題「{topic}」寫一篇吸引人的 IG 文案。

    規則：
    - 第一句必須能獨立成立，吸引滑手機的人停下來
    - 不要在開場就給答案，保持神秘感
    - 禁止用「——」
    - 禁止用「他笑著搖搖頭」「我愣住了」等 AI 感用語
    - 結尾加一句總結性金句
    - 拋出一個開放式問題引發討論
    - 語言自然，像在跟朋友聊天
    - 全文使用繁體中文
    - 標點符號使用全形（，。？！）
    """
    response = model.generate_content(prompt)
    return response.text

def update_notion_caption(page_id, caption):
    """把文案回寫到 Notion"""
    notion.pages.update(
        page_id=page_id,
        properties={
            "文案": {
                "rich_text": [{"text": {"content": caption}}]
            },
            "狀態": {
                "select": {"name": "生成中"}
            }
        }
    )

def main():
    pages = get_pending_pages()
    print(f"找到 {len(pages)} 筆待處理")

    for page in pages:
        page_id = page["id"]
        topic = page["properties"]["主題"]["title"][0]["text"]["content"]
        print(f"處理主題：{topic}")

        caption = generate_caption(topic)
        update_notion_caption(page_id, caption)
        print(f"✅ 文案已生成並回寫：{topic}")

if __name__ == "__main__":
    main()
