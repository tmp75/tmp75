"""Render a persistent ASCII portrait with self-contained, falling Matrix code."""

from hashlib import sha256
from html import escape
import random


def render_matrix_portrait(avatar, tones, x, y, width, height, *, animated=True):
    """Return an SVG fragment; the still portrait remains legible during animation.

    The moving code is rendered twice: faintly across the image and brightly
    through a fixed portrait luminance mask. Pass animated=False for a guaranteed
    static asset; the CSS media query also supports reduced motion where honored.
    """
    if not avatar or not max(map(len, avatar)):
        return ''
    rows, columns = len(avatar), max(map(len, avatar))
    if tones is not None and (len(tones) != rows or any(
            len(tone_row) != len(row) for tone_row, row in zip(tones, avatar))):
        raise ValueError('Portrait characters and tones must have matching dimensions.')
    cell_x, cell_y = width / columns, height / rows
    font_size = min(cell_x / .6, cell_y * .98)
    baseline = (cell_y - font_size) / 2 + font_size * .83
    unique = sha256(f'{x},{y},{width},{height}'.encode()).hexdigest()[:8]
    prefix = 'matrix-' + unique
    rng = random.Random(751998)
    glyphs = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ{}[]<>:/='
    padding = cell_y * 20
    parts = [
        f'<g transform="translate({x} {y})" font-family="Consolas, Liberation Mono, Menlo, monospace" aria-hidden="true">',
        '<defs>',
        f'<clipPath id="{prefix}-clip"><rect width="{width}" height="{height}"/></clipPath>',
        '<style>',
        f'@keyframes {prefix}-fall {{from {{transform: translateY(-{padding:.3f}px)}} '
        f'to {{transform: translateY({height:.3f}px)}}}}',
        f'.{prefix}-drop {{animation-name:{prefix}-fall;animation-timing-function:linear;animation-iteration-count:infinite;}}',
        f'@media (prefers-reduced-motion: reduce) {{.{prefix}-motion {{display:none}}}}',
        '</style>',
    ]

    # The mask is stationary while glyphs fall through it. Adjacent cells with
    # equal quantized tones share a rectangle to keep the SVG small.
    mask, base = [], []
    for row_index, raw_row in enumerate(avatar):
        row = raw_row.ljust(columns)
        if tones is None:
            tone_row = [40 if char.isspace() else 225 for char in row]
        else:
            tone_row = list(tones[row_index]) + [40] * (columns - len(raw_row))
        levels = [min(15, max(0, round((tone - 60) / 195 * 15))) for tone in tone_row]
        start = 0
        while start < columns:
            end = start + 1
            while end < columns and levels[end] == levels[start]:
                end += 1
            level = levels[start]
            if level:
                strength = level / 15
                green = round(68 + 152 * strength)
                red = round(7 + 39 * strength ** 2)
                blue = round(24 + 67 * strength)
                base.append(
                    f'<text x="{start * cell_x:.3f}" y="{row_index * cell_y + baseline:.3f}" '
                    f'fill="rgb({red},{green},{blue})" textLength="{(end-start) * cell_x:.3f}" '
                    f'lengthAdjust="spacingAndGlyphs">{escape(row[start:end])}</text>')
                gray = round(80 + 175 * strength)
                mask.append(
                    f'<rect x="{start * cell_x:.3f}" y="{row_index * cell_y:.3f}" '
                    f'width="{(end-start)*cell_x + .05:.3f}" height="{cell_y + .05:.3f}" '
                    f'fill="rgb({gray},{gray},{gray})"/>')
            start = end

    parts += [
        f'<mask id="{prefix}-portrait-mask" maskUnits="userSpaceOnUse" '
        f'x="0" y="0" width="{width}" height="{height}" style="mask-type:luminance">',
        *mask,
        '</mask>',
        f'<g id="{prefix}-streams" font-size="{font_size:.3f}">',
    ]
    # About 40 independent streams at desktop density, with staggered phases,
    # long fading tails, and pale leading characters. No flashing or scripts.
    for column in range(0, columns, 2):
        if rng.random() < .16:
            continue
        length = rng.randrange(8, 19)
        duration = rng.uniform(6.8, 13.8)
        phase = rng.uniform(0, duration)
        parts.append(
            f'<g class="{prefix}-drop" style="animation-duration:{duration:.3f}s;'
            f'animation-delay:-{phase:.3f}s">')
        for step in range(length):
            progress = step / (length - 1)
            color = '#dcffe8' if step == length - 1 else '#65ff95' if step == length - 2 else '#00ed65'
            opacity = .10 + .80 * progress ** 1.7
            char = rng.choice(glyphs)
            parts.append(
                f'<text x="{column*cell_x:.3f}" y="{step*cell_y + baseline:.3f}" '
                f'fill="{color}" opacity="{opacity:.3f}" textLength="{cell_x:.3f}" '
                f'lengthAdjust="spacingAndGlyphs">{escape(char)}</text>')
        parts.append('</g>')
    parts += ['</g>', '</defs>', f'<g clip-path="url(#{prefix}-clip)">']

    # Sparse stationary background code provides a coherent static/reduced-motion
    # appearance without the solid dotted backdrop of the original conversion.
    parts.append(f'<g fill="#063e21" font-size="{font_size:.3f}">')
    for row_index, raw_row in enumerate(avatar):
        if row_index % 2:
            continue
        for column in range(0, len(raw_row), 3):
            tone = tones[row_index][column] if tones is not None else (40 if raw_row[column].isspace() else 225)
            if tone <= 60 and rng.random() < .30:
                parts.append(
                    f'<text x="{column*cell_x:.3f}" y="{row_index*cell_y+baseline:.3f}" '
                    f'textLength="{cell_x:.3f}" lengthAdjust="spacingAndGlyphs">{rng.choice(glyphs[:36])}</text>')
    parts += ['</g>', f'<g font-size="{font_size:.3f}" xml:space="preserve">', *base, '</g>']
    if animated:
        parts += [f'<g class="{prefix}-motion">',
                  f'<use href="#{prefix}-streams" opacity=".20"/>',
                  f'<g mask="url(#{prefix}-portrait-mask)"><use href="#{prefix}-streams" opacity=".74"/></g>',
                  '</g>']
    parts += ['</g>', '</g>']
    return '\n'.join(parts)
