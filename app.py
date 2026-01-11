import streamlit as st
from PIL import Image
import os
import io
import textwrap

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Protein Alphabet Generator",
    layout="wide"
)

st.title("🧬 Protein Alphabet Text Generator")
st.write(
    "Render text using protein-structure letters (A–Z). "
    "This tool is intended for education, outreach, and scientific visualization."
)

# ---------------- DATA ----------------
IMAGE_DIR = "images"
protein_font = {chr(i): f"{chr(i)}.png" for i in range(65, 91)}

# Baseline correction (fraction of letter height)
BASELINE_SHIFT = {
    "L": 0.12,
    "I": 0.10,
    "J": 0.15,
    "T": 0.08,
}

# Scientifically grounded color palettes
# (single representative color or gradient endpoints)
COLOR_THEMES = {
    "Original": {
        "type": "none",
        "desc": "Original coloring from the rendered protein structure."
    },
    "Secondary structure (PyMOL-like)": {
        "type": "solid",
        "color": (220, 50, 50),  # helix-red inspired
        "desc": "Inspired by standard secondary-structure coloring (α-helices in red)."
    },
    "Hydrophobicity (Kyte–Doolittle)": {
        "type": "gradient",
        "low": (50, 80, 200),   # hydrophilic (blue)
        "high": (200, 50, 50),  # hydrophobic (red)
        "desc": "Blue → hydrophilic, Red → hydrophobic (Kyte–Doolittle inspired)."
    },
    "Electrostatics": {
        "type": "solid",
        "color": (130, 130, 230),
        "desc": "Blue tones inspired by electrostatic surface coloring."
    },
    "Protein core": {
        "type": "solid",
        "color": (120, 160, 120),
        "desc": "Muted green inspired by hydrophobic protein cores."
    },
    "Nucleic-acid binding": {
        "type": "solid",
        "color": (90, 160, 220),
        "desc": "Blue tones inspired by DNA/RNA-binding proteins."
    },
    "Neuroscience": {
        "type": "solid",
        "color": (160, 120, 200),
        "desc": "Purple tones inspired by brain and synaptic imagery."
    },
    "Infection / immunity": {
        "type": "solid",
        "color": (180, 140, 90),
        "desc": "Warm tones inspired by host–pathogen interactions."
    },
    "Grayscale (publication)": {
        "type": "solid",
        "color": (190, 190, 190),
        "desc": "Neutral grayscale for publication figures."
    },
    "High contrast (presentation)": {
        "type": "solid",
        "color": (255, 255, 255),
        "desc": "High-contrast white for dark backgrounds."
    },
}

# ---------------- SIDEBAR ----------------
st.sidebar.header("🎨 Appearance")

theme_name = st.sidebar.selectbox(
    "Color theme",
    list(COLOR_THEMES.keys())
)

max_chars_per_line = st.sidebar.slider(
    "Approx. characters per line", 10, 60, 30
)

# ---------------- UI ----------------
text = st.text_area(
    "Enter text",
    value="HELLO WORLD",
    height=120
)

letter_height = st.slider("Letter height (px)", 120, 400, 220)
letter_spacing = st.slider("Letter spacing (px)", 0, 60, 15)
word_spacing = st.slider("Word spacing (px)", 10, 120, 45)

# ---------------- COLOR UTILS ----------------
def apply_solid_color(img, color):
    overlay = Image.new("RGBA", img.size, (*color, 0))
    mask = img.split()[-1]
    overlay.putalpha(mask)
    return Image.alpha_composite(img, overlay)

def apply_gradient_color(img, low, high):
    width, height = img.size
    gradient = Image.new("RGBA", img.size)
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(low[0] * (1 - t) + high[0] * t)
        g = int(low[1] * (1 - t) + high[1] * t)
        b = int(low[2] * (1 - t) + high[2] * t)
        for x in range(width):
            gradient.putpixel((x, y), (r, g, b, 255))
    gradient.putalpha(img.split()[-1])
    return Image.alpha_composite(img, gradient)

# ---------------- RENDERING ----------------
def render_line(text, height, theme):
    glyphs = []

    for char in text.upper():
        if char == " ":
            spacer = Image.new("RGBA", (word_spacing, height), (0, 0, 0, 0))
            glyphs.append((spacer, 0))
            continue

        if char not in protein_font:
            continue

        path = os.path.join(IMAGE_DIR, protein_font[char])
        if not os.path.exists(path):
            continue

        img = Image.open(path).convert("RGBA")

        scale = height / img.height
        img = img.resize((int(img.width * scale), height), Image.LANCZOS)

        # Apply color theme
        theme_cfg = COLOR_THEMES[theme]
        if theme_cfg["type"] == "solid":
            img = apply_solid_color(img, theme_cfg["color"])
        elif theme_cfg["type"] == "gradient":
            img = apply_gradient_color(img, theme_cfg["low"], theme_cfg["high"])

        y_offset = int(BASELINE_SHIFT.get(char, 0) * height)
        glyphs.append((img, y_offset))

        spacer = Image.new("RGBA", (letter_spacing, height), (0, 0, 0, 0))
        glyphs.append((spacer, 0))

    if not glyphs:
        return None

    width = sum(img.width for img, _ in glyphs)
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    x = 0
    for img, y in glyphs:
        canvas.paste(img, (x, y), img)
        x += img.width

    return canvas

def render_text(text):
    wrapped_lines = textwrap.wrap(text, width=max_chars_per_line)
    line_images = [render_line(line, letter_height, theme_name) for line in wrapped_lines]
    line_images = [img for img in line_images if img is not None]

    if not line_images:
        return None

    spacing_y = 40
    total_height = sum(img.height for img in line_images) + spacing_y * (len(line_images) - 1)
    width = max(img.width for img in line_images)

    canvas = Image.new("RGBA", (width, total_height), (0, 0, 0, 0))

    y = 0
    for img in line_images:
        x = (width - img.width) // 2
        canvas.paste(img, (x, y), img)
        y += img.height + spacing_y

    return canvas

# ---------------- RENDER + EXPORT ----------------
if text.strip():
    final_img = render_text(text)

    if final_img:
        st.subheader("Rendered output")
        st.image(final_img)

        buf = io.BytesIO()
        final_img.save(buf, format="PNG")
        buf.seek(0)

        st.download_button(
            "⬇️ Download PNG",
            data=buf,
            file_name="protein_text.png",
            mime="image/png"
        )

# ---------------- EDUCATIONAL SECTION ----------------
st.markdown("---")
with st.expander("📘 Educational notes"):
    st.markdown(
        f"""
**What are you seeing?**  
Each letter corresponds to a real protein structure whose 3D fold resembles a typographic character.

**Why line wrapping matters**  
Proteins are rendered as images, so text layout must be handled explicitly (unlike normal fonts).

**About the selected color theme**  
{COLOR_THEMES[theme_name]['desc']}
"""
    )

# ---------------- REFERENCE ----------------
st.markdown("---")
st.markdown(
    """
**Source reference**  
Howarth, M. (2015). *Say it with proteins: an alphabet of crystal structures*.  
**Nature Structural & Molecular Biology**, 22(5), 349–349.  
🔗 https://www.nature.com/articles/nsmb.3011
""",
    unsafe_allow_html=True
)
