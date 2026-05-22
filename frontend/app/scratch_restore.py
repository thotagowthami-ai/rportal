from pathlib import Path

page_path = Path(__file__).resolve().parent / "page.tsx"

with page_path.open('r', encoding='utf-8') as f:
    content = f.read()

parts = content.split('      {/* SPLIT: ')
if len(parts) < 5:
    raise ValueError("Expected at least 4 SPLIT markers in page.tsx layout content.")

part_linkedin = parts[1]
part_careers = parts[2]
part_scoring = parts[3]

pipeline_and_rest = parts[4].split('      {/* CTA BANNER */}')
if len(pipeline_and_rest) < 2:
    raise ValueError("Expected 'CTA BANNER' marker in page.tsx layout content.")

part_pipeline = pipeline_and_rest[0]
rest = '      {/* CTA BANNER */}' + pipeline_and_rest[1]

new_content = parts[0] + \
    '      {/* SPLIT: AI SCORING */}' + part_scoring + \
    '      {/* SPLIT: CANDIDATE PIPELINE */}' + part_pipeline + \
    '      {/* SPLIT: LINKEDIN AI */}' + part_linkedin + \
    '      {/* SPLIT: PUBLIC CAREERS */}' + part_careers + \
    rest

import re
new_content = new_content.replace(' id="features"', '')
new_content = re.sub(r'(<section className=\"py-24 px-6 bg-\[#fdf8f3\]\")>', r'\1 id="features">', new_content, count=1)

with page_path.open('w', encoding='utf-8') as f:
    f.write(new_content)
print('Done reordering to match the original!')
