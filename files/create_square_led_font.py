#!/usr/bin/env python3
"""
LED Dot Matrix Font Creator - Square Block Version
Creates TTF fonts with square LED blocks like airport terminal displays
"""

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

# Font metrics
UNITS_PER_EM = 1000
ASCENT = 800
DESCENT = -200

# Grid settings - matching the reference image
BLOCK_SIZE = 70  # Size of each square block
BLOCK_GAP = 10   # Small gap between blocks (tight spacing like reference)
BLOCK_SPACING = BLOCK_SIZE + BLOCK_GAP  # Total spacing between block centers

# Colors (RGBA format for COLR fonts)
# "off" blocks - dark gray with full opacity
COLOR_OFF = (50, 50, 50, 255)

# 7 blocks wide (including padding), 7 blocks tall
GRID_WIDTH = 7
GRID_HEIGHT = 7
CHAR_WIDTH = GRID_WIDTH * BLOCK_SPACING

# Padding columns (first and last columns are always "off")
PADDING_COLS = [0, 6]  # First and last column indices

# 5x7 dot matrix patterns for each character (only the active 5 columns)
CHAR_PATTERNS = {
    'A': [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
    ],
    'B': [
        [1, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 0],
    ],
    'C': [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 1],
        [0, 1, 1, 1, 0],
    ],
    'D': [
        [1, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 0],
    ],
    'E': [
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 1, 1, 1, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
    ],
    'F': [
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 1, 1, 1, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
    ],
    'G': [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 0],
        [1, 0, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 1, 1, 0],
    ],
    'H': [
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
    ],
    'I': [
        [0, 1, 1, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 1, 0],
    ],
    'J': [
        [0, 0, 1, 1, 1],
        [0, 0, 0, 1, 0],
        [0, 0, 0, 1, 0],
        [0, 0, 0, 1, 0],
        [1, 0, 0, 1, 0],
        [1, 0, 0, 1, 0],
        [0, 1, 1, 0, 0],
    ],
    'K': [
        [1, 0, 0, 0, 1],
        [1, 0, 0, 1, 0],
        [1, 0, 1, 0, 0],
        [1, 1, 0, 0, 0],
        [1, 0, 1, 0, 0],
        [1, 0, 0, 1, 0],
        [1, 0, 0, 0, 1],
    ],
    'L': [
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
    ],
    'M': [
        [1, 0, 0, 0, 1],
        [1, 1, 0, 1, 1],
        [1, 0, 1, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
    ],
    'N': [
        [1, 0, 0, 0, 1],
        [1, 1, 0, 0, 1],
        [1, 0, 1, 0, 1],
        [1, 0, 0, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
    ],
    'O': [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 1, 1, 0],
    ],
    'P': [
        [1, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
    ],
    'Q': [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 1, 0, 1],
        [1, 0, 0, 1, 0],
        [0, 1, 1, 0, 1],
    ],
    'R': [
        [1, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 0],
        [1, 0, 1, 0, 0],
        [1, 0, 0, 1, 0],
        [1, 0, 0, 0, 1],
    ],
    'S': [
        [0, 1, 1, 1, 1],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 1],
        [0, 0, 0, 0, 1],
        [1, 1, 1, 1, 0],
    ],
    'T': [
        [1, 1, 1, 1, 1],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
    ],
    'U': [
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 1, 1, 0],
    ],
    'V': [
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 0, 1, 0],
        [0, 0, 1, 0, 0],
    ],
    'W': [
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 1, 0, 1],
        [1, 1, 0, 1, 1],
        [1, 0, 0, 0, 1],
    ],
    'X': [
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 0, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 0, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
    ],
    'Y': [
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 0, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
    ],
    'Z': [
        [1, 1, 1, 1, 1],
        [0, 0, 0, 0, 1],
        [0, 0, 0, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
    ],
    '0': [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 1, 1],
        [1, 0, 1, 0, 1],
        [1, 1, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 1, 1, 0],
    ],
    '1': [
        [0, 0, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 1, 0],
    ],
    '2': [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [0, 0, 0, 0, 1],
        [0, 0, 0, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [1, 1, 1, 1, 1],
    ],
    '3': [
        [1, 1, 1, 1, 0],
        [0, 0, 0, 0, 1],
        [0, 0, 0, 0, 1],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 1],
        [0, 0, 0, 0, 1],
        [1, 1, 1, 1, 0],
    ],
    '4': [
        [0, 0, 0, 1, 0],
        [0, 0, 1, 1, 0],
        [0, 1, 0, 1, 0],
        [1, 0, 0, 1, 0],
        [1, 1, 1, 1, 1],
        [0, 0, 0, 1, 0],
        [0, 0, 0, 1, 0],
    ],
    '5': [
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0],
        [1, 1, 1, 1, 0],
        [0, 0, 0, 0, 1],
        [0, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 1, 1, 0],
    ],
    '6': [
        [0, 0, 1, 1, 0],
        [0, 1, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 1, 1, 0],
    ],
    '7': [
        [1, 1, 1, 1, 1],
        [0, 0, 0, 0, 1],
        [0, 0, 0, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0],
    ],
    '8': [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 1, 1, 0],
    ],
    '9': [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 1, 1, 1],
        [0, 0, 0, 0, 1],
        [0, 0, 0, 1, 0],
        [0, 1, 1, 0, 0],
    ],
    ' ': [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ],
    '.': [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 1, 0, 0],
    ],
    ',': [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 0, 0, 0],
    ],
    '!': [
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
    ],
    '?': [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [0, 0, 0, 0, 1],
        [0, 0, 0, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
    ],
    '-': [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ],
    ':': [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0],
    ],
}

def draw_square_block(pen, x, y, size):
    """Draw a square block with counter-clockwise winding (TrueType standard)"""
    pen.moveTo((x, y))
    pen.lineTo((x, y + size))
    pen.lineTo((x + size, y + size))
    pen.lineTo((x + size, y))
    pen.closePath()

def create_layer_glyph(pattern, layer_type, debug_char=None):
    """Create a glyph layer for either 'on' or 'off' blocks

    Args:
        pattern: 5x7 pattern for the active area
        layer_type: 'on' or 'off' - determines which blocks to draw
        debug_char: Optional character for debugging output
    """
    pen = TTGlyphPen(None)
    block_count = 0

    # Create full 7x7 grid with padding columns
    for row in range(GRID_HEIGHT):
        for col in range(GRID_WIDTH):
            x = col * BLOCK_SPACING
            # Start from top
            y = ASCENT - (row * BLOCK_SPACING) - BLOCK_SIZE

            # Check if this is a padding column
            is_padding = col in PADDING_COLS

            # Check if this is an "on" block in the active area
            is_on = False
            if not is_padding and row < 7:
                active_col = col - 1  # Offset by 1 for the left padding column
                if 0 <= active_col < 5:
                    is_on = pattern[row][active_col] == 1

            if layer_type == 'on' and is_on:
                # Full size block for "on" pixels
                draw_square_block(pen, x, y, BLOCK_SIZE)
                block_count += 1
            elif layer_type == 'off' and not is_on:
                # Full size block for "off" pixels (same size as "on")
                draw_square_block(pen, x, y, BLOCK_SIZE)
                block_count += 1

    if debug_char:
        print(f"    {layer_type} layer: {block_count} blocks")

    return pen.glyph()

def create_font(color_name, color_on_rgb):
    """Create COLR LED font with specified 'on' color

    Args:
        color_name: Name for the font (e.g., 'green', 'white')
        color_on_rgb: RGB tuple for "on" blocks (e.g., (46, 204, 112))
    """
    print(f"Creating COLR LED Terminal Font - {color_name}...")

    fb = FontBuilder(UNITS_PER_EM, isTTF=True)

    # Set font metadata
    fb.setupHead(unitsPerEm=UNITS_PER_EM, created=0, modified=0)

    fb.setupNameTable(dict(
        familyName=f"LED Terminal {color_name.title()}",
        styleName="Regular",
        uniqueFontIdentifier=f"LEDTerminal{color_name}-Regular-COLR",
        fullName=f"LED Terminal {color_name.title()} Regular",
        version="3.0",
        psName=f"LEDTerminal{color_name}-Regular",
        manufacturer="Custom Generated",
        designer="LED Matrix Generator",
        description=f"Color LED dot matrix font ({color_name}) with embedded colors via COLR",
    ))

    # Create glyphs
    glyphs = {}
    advanceWidths = {}
    characterMap = {}
    color_layers = {}

    # Create .notdef glyph
    pen = TTGlyphPen(None)
    glyphs['.notdef'] = pen.glyph()
    advanceWidths['.notdef'] = (CHAR_WIDTH, 0)

    # Create all character glyphs with color layers
    for char, pattern in CHAR_PATTERNS.items():
        glyph_name = f"uni{ord(char):04X}" if char != ' ' else "space"
        on_layer_name = f"{glyph_name}.on"
        off_layer_name = f"{glyph_name}.off"

        # Create "on" blocks layer
        glyphs[on_layer_name] = create_layer_glyph(pattern, 'on', char)
        advanceWidths[on_layer_name] = (CHAR_WIDTH, 0)

        # Create "off" blocks layer
        glyphs[off_layer_name] = create_layer_glyph(pattern, 'off', char)
        advanceWidths[off_layer_name] = (CHAR_WIDTH, 0)

        # Create base glyph (empty, just for COLR reference)
        pen = TTGlyphPen(None)
        glyphs[glyph_name] = pen.glyph()
        advanceWidths[glyph_name] = (CHAR_WIDTH, 0)

        # Define color layers: [layer_name, palette_index]
        # Palette index 0 = "on" color, index 1 = "off" color
        color_layers[glyph_name] = [
            (off_layer_name, 1),  # Draw "off" blocks first (background)
            (on_layer_name, 0),   # Draw "on" blocks on top
        ]

        characterMap[ord(char)] = glyph_name
        print(f"  Created glyph: {char} ({glyph_name}) with color layers")

    # Setup glyph order
    all_glyphs = ['.notdef'] + list(characterMap.values())
    for char_glyph in characterMap.values():
        all_glyphs.append(f"{char_glyph}.on")
        all_glyphs.append(f"{char_glyph}.off")

    fb.setupGlyphOrder(all_glyphs)
    fb.setupCharacterMap(characterMap)
    fb.setupHorizontalMetrics(advanceWidths)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)

    fb.setupOS2(
        sTypoAscender=ASCENT,
        sTypoDescender=DESCENT,
        sTypoLineGap=0,
        usWinAscent=ASCENT,
        usWinDescent=-DESCENT,
    )

    fb.setupPost()

    # Setup COLR table with color palette
    # Palette: [on_color, off_color]
    # CPAL requires colors normalized to 0-1 range
    color_on_normalized = tuple(c / 255.0 for c in color_on_rgb) + (1.0,)  # RGB + alpha
    color_off_normalized = tuple(c / 255.0 for c in COLOR_OFF)  # Already has alpha
    palette = [color_on_normalized, color_off_normalized]

    fb.setupCOLR(color_layers)
    fb.setupCPAL([palette])

    # Build and save
    font = fb.font
    output_path = f"/Users/tommylowry/Documents/patriot-center/patriot_center_frontend/src/fonts/LED-Terminal_{color_name}.ttf"
    font.save(output_path)
    print(f"✓ COLR Font created: {output_path}\n")

    return output_path

if __name__ == "__main__":
    print("="*60)
    print("COLR LED TERMINAL FONT GENERATOR v3.0")
    print("Color fonts with embedded 'on' and 'off' block colors")
    print("="*60)
    print()

    # Create both color versions
    # Green: #2ecc70 = RGB(46, 204, 112)
    # White: #c8c8c8 = RGB(200, 200, 200)
    green_path = create_font("green", (46, 204, 112))
    white_path = create_font("white", (200, 200, 200))

    print("="*60)
    print("COLR FONTS CREATED SUCCESSFULLY!")
    print("="*60)
    print(f"1. LED-Terminal_green.ttf (on=#2ecc70, off=#323232)")
    print(f"2. LED-Terminal_white.ttf (on=#c8c8c8, off=#323232)")
    print()
    print("These are COLR color fonts with embedded colors.")
    print("The browser will render 'on' and 'off' blocks in")
    print("their designated colors automatically.")
    print("="*60)
