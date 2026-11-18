# -*- coding: utf-8 -*-
"""
Creates public/index.html with shareable links to all generated charts.
"""

import os
from datetime import datetime, timezone

AIRPORTS = ["VABB", "VAAU", "VAPO", "VANP"]
PUBLIC_DIR = "public"

cards = []

for icao_code in AIRPORTS:
    filename = f"meteograph_{icao_code}.png"
    file_path = os.path.join(PUBLIC_DIR, filename)

    if os.path.exists(file_path):
        cards.append(f"""
        <a class="card" href="./{filename}" target="_blank" rel="noopener">
            <img src="./{filename}" alt="{icao_code} meteograph">
            <h2>{icao_code}</h2>
            <p>Open full-size chart</p>
        </a>
        """)

html = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Daily METAR Meteographs</title>

    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #f4f6f8;
            margin: 0;
            padding: 24px;
        }}

        h1 {{
            text-align: center;
        }}

        .updated {{
            text-align: center;
            color: #555;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            max-width: 1400px;
            margin: auto;
        }}

        .card {{
            background: white;
            border-radius: 12px;
            padding: 14px;
            text-decoration: none;
            color: #111;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
        }}

        .card img {{
            width: 100%;
            border-radius: 8px;
        }}

        .card h2 {{
            margin: 0.5rem 0 0.2rem;
        }}

        .card p {{
            margin: 0;
            color: #555;
        }}
    </style>
</head>

<body>
    <h1>Daily METAR Meteographs</h1>
    <p class="updated">
        Generated: {datetime.now(timezone.utc):%d %B %Y, %H:%M UTC}
    </p>

    <div class="grid">
        {''.join(cards)}
    </div>
</body>

</html>
"""

os.makedirs(PUBLIC_DIR, exist_ok=True)

index_path = os.path.join(PUBLIC_DIR, "index.html")

with open(index_path, "w", encoding="utf-8") as file:
    file.write(html)

print(f"Created: {index_path}")