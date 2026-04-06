from PIL import Image, ImageDraw, ImageFont
import textwrap

def generate_quote_image(main_text, sub_text, output_path="output.png"):
    # 畫布設定
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), color=(10, 10, 10))
    draw = ImageDraw.Draw(img)

    # 字型（GitHub Actions 用系統字型）
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 主文字（白色）
    lines = textwrap.wrap(main_text, width=12)
    y = 300
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_big)
        w = bbox[2] - bbox[0]
        draw.text(((W - w) / 2, y), line, font=font_big, fill=(255, 255, 255))
        y += 90

    # 副文字（金色）
    bbox = draw.textbbox((0, 0), sub_text, font=font_small)
    w = bbox[2] - bbox[0]
    draw.text(((W - w) / 2, y + 40), sub_text, font=font_small, fill=(212, 175, 55))

    img.save(output_path)
    print(f"圖片已生成：{output_path}")
