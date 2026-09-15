#!/usr/bin/env python3
import sys
from pathlib import Path

out = Path(sys.argv[1] if len(sys.argv) > 1 else 'caption-card.svg')
out.parent.mkdir(parents=True, exist_ok=True)

# Transparent rounded black card sized for the 1080x1920 Shorts canvas.
svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="940" height="250" viewBox="0 0 940 250">
<rect x="2" y="2" width="936" height="246" rx="38" ry="38"
      fill="#050505" fill-opacity="0.82" stroke="#FFFFFF" stroke-opacity="0.08" stroke-width="4"/>
</svg>'''
out.write_text(svg, encoding='utf-8')
print(out)
