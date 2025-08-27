import fitz  # PyMuPDF
from PIL import Image, ImageEnhance, ImageOps
import argparse, io

def darken_top_strip(pdf_path, output_path, strip_height=100, contrast_factor=2.5, brightness_factor=0.6):
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        w, h = img.size

        # Define top strip region
        box = (0, 0, w, strip_height)

        # Crop and darken
        region = img.crop(box)
        region = ImageEnhance.Brightness(region).enhance(brightness_factor)
        region = ImageEnhance.Contrast(region).enhance(contrast_factor)
        region = ImageOps.autocontrast(region)

        # Paste back
        img.paste(region, box)

        # Replace page with processed image
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        rect = fitz.Rect(0, 0, w, h)
        page.insert_image(rect, stream=img_bytes.getvalue())

    doc.save(output_path)
    doc.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to input PDF")
    parser.add_argument("--output", required=True, help="Path to output PDF")
    parser.add_argument("--strip_height", type=int, default=100, help="Height of top strip to darken")
    args = parser.parse_args()

    darken_top_strip(args.input, args.output, strip_height=args.strip_height)