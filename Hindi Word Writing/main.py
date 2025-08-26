from PIL import Image, ImageDraw, ImageFont
# 1) Create a sample image
img = Image.new("RGB", (600, 400), "white")
draw = ImageDraw.Draw(img)
text = "लाइटें"
# 2) Try to find a Devanagari-capable font across OSes
candidate_fonts = [
    # Windows (try all common Noto Sans Devanagari filename variants)
    r"C:\Windows\Fonts\NotoSansDevanagari-Regular.ttf",
    r"C:\Windows\Fonts\NotoSansDevanagari.ttf",
    r"C:\Windows\Fonts\Noto Sans Devanagari.ttf",
    r"C:\Windows\Fonts\Mangal.ttf",                      # Mangal font (very common for Hindi)
    r"C:\Windows\Fonts\Nirmala.ttf",                     # Sometimes present
    r"C:\Windows\Fonts\Nirmala UI.ttf",                  # Correct Nirmala UI font
    r"C:\Windows\Fonts\NirmalaB.ttf",
    # macOS
    "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc",
    "/System/Library/Fonts/Supplemental/KohinoorDevanagari.ttc",
    # Linux (common Noto path)
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
    "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf",
]
font_path = None
for path in candidate_fonts:
    try:
        open(path, "rb").close()
        font_path = path
        break
    except Exception:
        continue
if font_path:
    print(f"Using font: {font_path}")
else:
    print("No Devanagari-capable font found. Using default font (will NOT render Hindi correctly)")

 # 3) Load font (use RAQM layout engine if available for proper shaping)
layout_engine = getattr(ImageFont, "LAYOUT_RAQM", None)
if font_path:
    try:
        if layout_engine:
            font = ImageFont.truetype(font_path, size=60, layout_engine=layout_engine)
        else:
            font = ImageFont.truetype(font_path, size=60)
    except Exception as e:
        print(f"Error loading font: {e}. Falling back to default font.")
        font = ImageFont.load_default()
else:
    # Fallback: default font will NOT render Devanagari correctly
    font = ImageFont.load_default()
# 4) Draw the Hindi text at (200, 200)
draw.text((200, 200), text, fill="black", font=font)
# 5) Save or show
img.save("sample_hindi_text.png")
print("Saved to sample_hindi_text.png")
