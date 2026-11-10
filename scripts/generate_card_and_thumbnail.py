"""
Generate high-fidelity, professional Card Banner (1200x630) and Thumbnail (512x512)
for the Gemma 4 Developer Agent Paper Track.
Saves directly to C:\\Users\\Ronak Jain\\Downloads\\
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DOWNLOADS_DIR = r"C:\Users\Ronak Jain\Downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_REGULAR = r"C:\Windows\Fonts\segoeui.ttf"
FONT_MONO = r"C:\Windows\Fonts\consolab.ttf"

def draw_radial_gradient(draw, width, height, center_x, center_y, radius, start_color, end_color):
    """Draw a smooth radial glow on an overlay image."""
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    for r in range(radius, 0, -6):
        alpha = int(start_color[3] * (1.0 - (r / radius) ** 1.5))
        color = (start_color[0], start_color[1], start_color[2], alpha)
        ov_draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], fill=color)
    return overlay

# =============================================================================
# 1. CARD BANNER (1200 x 630)
# =============================================================================
def generate_card_banner():
    W, H = 1200, 630
    img = Image.new("RGBA", (W, H), (11, 15, 25, 255))
    
    # Background subtle linear gradient
    for y in range(H):
        ratio = y / H
        r = int(10 + ratio * 12)
        g = int(14 + ratio * 16)
        b = int(26 + ratio * 24)
        for x in range(0, W, 2):
            img.putpixel((x, y), (r, g, b, 255))
            if x + 1 < W:
                img.putpixel((x + 1, y), (r, g, b, 255))

    # Glow overlays
    glow_cyan = draw_radial_gradient(None, W, H, 950, 180, 420, (56, 189, 248, 80), (15, 23, 42, 0))
    glow_purple = draw_radial_gradient(None, W, H, 200, 520, 380, (147, 51, 234, 60), (15, 23, 42, 0))
    img = Image.alpha_composite(img, glow_cyan)
    img = Image.alpha_composite(img, glow_purple)

    draw = ImageDraw.Draw(img)

    # Subtle tech grid lines
    grid_color = (30, 41, 59, 100)
    for x in range(0, W, 50):
        draw.line([(x, 0), (x, H)], fill=grid_color, width=1)
    for y in range(0, H, 50):
        draw.line([(0, y), (W, y)], fill=grid_color, width=1)

    # Fonts
    font_category = ImageFont.truetype(FONT_BOLD, 18)
    font_title1 = ImageFont.truetype(FONT_BOLD, 52)
    font_title2 = ImageFont.truetype(FONT_BOLD, 48)
    font_subtitle = ImageFont.truetype(FONT_REGULAR, 23)
    font_badge = ImageFont.truetype(FONT_BOLD, 16)
    font_mono = ImageFont.truetype(FONT_MONO, 15)

    # 1. Top Category Badge
    pill_text = "GOOGLE GEMMA 4 · PAPER TRACK 2026"
    draw.rounded_rectangle([70, 70, 470, 110], radius=20, fill=(14, 116, 144, 60), outline=(56, 189, 248, 220), width=2)
    # glowing dot
    draw.ellipse([88, 85, 96, 93], fill=(56, 189, 248, 255))
    draw.text((108, 79), pill_text, fill=(224, 242, 254, 255), font=font_category)

    # 2. Main Title
    draw.text((70, 145), "BOUNDED RATIONALITY IN", fill=(255, 255, 255, 255), font=font_title1)
    draw.text((70, 210), "AUTONOMOUS CODING AGENTS", fill=(56, 189, 248, 255), font=font_title2)

    # 3. Subtitle / Abstract hook
    draw.text((70, 285), "Empirical Failure Taxonomy and Architectural Stabilization", fill=(226, 232, 240, 255), font=font_subtitle)
    draw.text((70, 320), "of Quantized Gemma 4 12B on SWE-bench", fill=(148, 163, 184, 255), font=font_subtitle)

    # 4. Feature Badges (3 horizontal cards)
    badges = [
        ("NVIDIA L4 · INT4 QAT", (16, 185, 129, 255), "⚡"),
        ("Inter-Turn Thought Stripping", (168, 85, 247, 255), "🛡️"),
        ("10h Bounded Execution Cap", (56, 189, 248, 255), "⏱️")
    ]
    bx = 70
    by = 405
    for label, dot_color, icon in badges:
        bw = 250
        bh = 46
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=12, fill=(30, 41, 59, 180), outline=(71, 85, 105, 180), width=1)
        draw.ellipse([bx + 16, by + 18, bx + 26, by + 28], fill=dot_color)
        draw.text((bx + 36, by + 12), label, fill=(241, 245, 249, 255), font=font_badge)
        bx += bw + 20

    # 5. Verified Metadata Footer
    footer_text = "Verified Artifact: SHA-256 82a9478d... | Evaluated on SWE-bench Official Manifest (129 Tasks)"
    draw.text((70, 560), footer_text, fill=(100, 116, 139, 255), font=font_mono)

    # 6. Right-Side Hexagonal Cybernetic Graphics
    cx, cy = 960, 320
    # Concentric rings
    for radius in [210, 160, 110]:
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=(56, 189, 248, 50), width=1)
    
    # Stylized Hexagon
    hex_pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = cx + 130 * math.cos(angle)
        py = cy + 130 * math.sin(angle)
        hex_pts.append((px, py))
    draw.polygon(hex_pts, fill=(15, 23, 42, 160), outline=(56, 189, 248, 220))

    # Inner core brackets
    font_brackets = ImageFont.truetype(FONT_BOLD, 46)
    draw.text((cx - 40, cy - 35), "< / >", fill=(129, 140, 248, 255), font=font_brackets)
    
    # 4 Orbiting Tool Nodes
    nodes = [
        (cx - 160, cy - 80, "run_command"),
        (cx + 120, cy - 110, "submit_patch"),
        (cx - 130, cy + 120, "edit_file"),
        (cx + 110, cy + 100, "1024_budget")
    ]
    font_node = ImageFont.truetype(FONT_MONO, 12)
    for nx, ny, nlabel in nodes:
        draw.rounded_rectangle([nx - 55, ny - 14, nx + 55, ny + 14], radius=8, fill=(15, 23, 42, 220), outline=(99, 102, 241, 200), width=1)
        draw.text((nx - 45, ny - 8), nlabel, fill=(199, 210, 254, 255), font=font_node)
        # connector line
        draw.line([(nx, ny), (cx, cy)], fill=(99, 102, 241, 60), width=1)

    out_path = os.path.join(DOWNLOADS_DIR, "gemma4_paper_card_banner.png")
    img.save(out_path, "PNG", quality=95)
    print(f"Card Banner saved to: {out_path}")
    return out_path

# =============================================================================
# 2. THUMBNAIL (512 x 512)
# =============================================================================
def generate_thumbnail():
    S = 512
    img = Image.new("RGBA", (S, S), (11, 15, 25, 255))

    # Radial glow in center
    glow = draw_radial_gradient(None, S, S, S//2, S//2 - 20, 240, (56, 189, 248, 110), (15, 23, 42, 0))
    glow_violet = draw_radial_gradient(None, S, S, S//2, S//2 + 80, 180, (147, 51, 234, 80), (15, 23, 42, 0))
    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, glow_violet)

    draw = ImageDraw.Draw(img)

    # Hexagonal Shield in Center
    cx, cy = S // 2, 195
    hex_pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = cx + 115 * math.cos(angle)
        py = cy + 115 * math.sin(angle)
        hex_pts.append((px, py))
    draw.polygon(hex_pts, fill=(15, 23, 42, 220), outline=(56, 189, 248, 255))
    
    # Outer accent ring
    draw.ellipse([cx - 135, cy - 135, cx + 135, cy + 135], outline=(99, 102, 241, 100), width=2)

    # Brackets inside hex
    font_code = ImageFont.truetype(FONT_BOLD, 48)
    draw.text((cx - 42, cy - 36), "< / >", fill=(56, 189, 248, 255), font=font_code)

    # Floating Spark
    draw.text((cx - 10, cy - 75), "✦", fill=(244, 114, 182, 255), font=ImageFont.truetype(FONT_BOLD, 22))

    # Text hierarchy below badge
    font_t1 = ImageFont.truetype(FONT_BOLD, 36)
    font_t2 = ImageFont.truetype(FONT_BOLD, 26)
    font_sub = ImageFont.truetype(FONT_REGULAR, 17)
    font_tag = ImageFont.truetype(FONT_BOLD, 13)

    # "GEMMA 4"
    t1 = "GEMMA 4"
    bbox1 = draw.textbbox((0, 0), t1, font=font_t1)
    w1 = bbox1[2] - bbox1[0]
    draw.text(((S - w1) // 2, 330), t1, fill=(255, 255, 255, 255), font=font_t1)

    # "SWE-AGENT"
    t2 = "SWE AGENT"
    bbox2 = draw.textbbox((0, 0), t2, font=font_t2)
    w2 = bbox2[2] - bbox2[0]
    draw.text(((S - w2) // 2, 375), t2, fill=(56, 189, 248, 255), font=font_t2)

    # Tag: "BOUNDED RATIONALITY"
    tag = "BOUNDED RATIONALITY"
    bbox_tag = draw.textbbox((0, 0), tag, font=font_tag)
    wtag = bbox_tag[2] - bbox_tag[0]
    bx = (S - wtag) // 2
    draw.rounded_rectangle([bx - 14, 430, bx + wtag + 14, 460], radius=15, fill=(30, 41, 59, 220), outline=(56, 189, 248, 180), width=1)
    draw.text((bx, 437), tag, fill=(224, 242, 254, 255), font=font_tag)

    # Subtitle: "KAGGLE PAPER TRACK"
    sub = "KAGGLE PAPER TRACK 2026"
    bbox_sub = draw.textbbox((0, 0), sub, font=font_sub)
    wsub = bbox_sub[2] - bbox_sub[0]
    draw.text(((S - wsub) // 2, 475), sub, fill=(148, 163, 184, 255), font=font_sub)

    out_path = os.path.join(DOWNLOADS_DIR, "gemma4_paper_thumbnail.png")
    img.save(out_path, "PNG", quality=95)
    print(f"Thumbnail saved to: {out_path}")
    return out_path

if __name__ == "__main__":
    b_path = generate_card_banner()
    t_path = generate_thumbnail()
    print("ALL ASSETS GENERATED SUCCESSFULLY!")

