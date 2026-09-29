"""
Asset generator for Keyboard Fixer.
Creates an elegant modern keyboard icon with FA/EN indicator.
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon():
    os.makedirs("assets", exist_ok=True)
    icon_path = os.path.join("assets", "icon.png")
    ico_path = os.path.join("assets", "icon.ico")
    
    # 256x256 high-resolution icon
    size = (256, 256)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Modern squircle background with gradient-like look (deep indigo/cyan theme)
    # Background rounded rectangle
    bg_color = (24, 28, 38, 255) # Deep sleek dark navy
    draw.rounded_rectangle([(12, 12), (244, 244)], radius=56, fill=bg_color)
    
    # Glowing border
    border_color = (59, 130, 246, 220) # Bright Accent Blue
    draw.rounded_rectangle([(12, 12), (244, 244)], radius=56, outline=border_color, width=6)
    
    # Draw a stylized modern keyboard frame
    kb_bg = (35, 42, 58, 255)
    draw.rounded_rectangle([(38, 52), (218, 204)], radius=24, fill=kb_bg, outline=(70, 85, 120, 180), width=3)
    
    # Draw stylized keycaps
    # Row 1 (small keys)
    keys_r1 = [(52, 68, 76, 92), (84, 68, 108, 92), (116, 68, 140, 92), (148, 68, 172, 92), (180, 68, 204, 92)]
    for box in keys_r1:
        draw.rounded_rectangle(box, radius=6, fill=(50, 60, 85, 255))
        
    # Row 2 (Middle keys - FA & EN highlighted)
    # Key Left (EN)
    draw.rounded_rectangle([(52, 104), (108, 148)], radius=10, fill=(37, 99, 235, 255)) # Vibrant Blue
    # Key Right (FA)
    draw.rounded_rectangle([(148, 104), (204, 148)], radius=10, fill=(16, 185, 129, 255)) # Vibrant Emerald
    
    # Draw double arrow between them
    draw.polygon([(118, 126), (138, 126), (133, 121)], fill=(220, 230, 245, 255))
    draw.polygon([(138, 126), (118, 126), (123, 131)], fill=(220, 230, 245, 255))
    
    # Row 3 (Spacebar row)
    draw.rounded_rectangle([(52, 160), (84, 188)], radius=8, fill=(50, 60, 85, 255))
    draw.rounded_rectangle([(92, 160), (164, 188)], radius=8, fill=(70, 85, 120, 255)) # Spacebar
    draw.rounded_rectangle([(172, 160), (204, 188)], radius=8, fill=(50, 60, 85, 255))

    # Text annotations on keycaps
    try:
        font_en = ImageFont.truetype("arial.ttf", 22)
        font_fa = ImageFont.truetype("tahoma.ttf", 20)
        draw.text((64, 114), "EN", font=font_en, fill=(255, 255, 255, 255))
        draw.text((160, 112), "FA", font=font_fa, fill=(255, 255, 255, 255))
    except Exception:
        # Fallback if font missing
        draw.text((64, 114), "EN", fill=(255, 255, 255, 255))
        draw.text((160, 112), "FA", fill=(255, 255, 255, 255))

    img.save(icon_path, "PNG")
    # Also save as .ico
    img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Icons saved to {icon_path} and {ico_path}")

if __name__ == "__main__":
    create_app_icon()
