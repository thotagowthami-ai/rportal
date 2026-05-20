with open('c:/Users/GOWTHAMI/Downloads/projects/recruiting-platform/frontend/app/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

parts = content.split('      {/* SPLIT: ')

public_careers_and_rest = parts[4].split('      {/* CTA BANNER */}', 1)
public_careers = public_careers_and_rest[0]
rest = '      {/* CTA BANNER */}' + public_careers_and_rest[1]

new_content = parts[0] + \
    '      {/* SPLIT: LINKEDIN AI */}' + parts[3].replace('id="features"', '') + \
    '      {/* SPLIT: PUBLIC CAREERS */}' + public_careers + \
    '      {/* SPLIT: AI SCORING */}' + parts[1].replace('id="features"', '') + \
    '      {/* SPLIT: CANDIDATE PIPELINE */}' + parts[2] + \
    rest

import re
new_content = re.sub(r'(<section className=\"py-24 px-6 bg-\[#fdf8f3\]\")>', r'\1 id="features">', new_content, count=1)

with open('c:/Users/GOWTHAMI/Downloads/projects/recruiting-platform/frontend/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(new_content)
print('Done!')
