import os
def search(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.tsx') or file.endswith('.ts'):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'api/linkedin/connect' in content or '/linkedin/connect' in content:
                        print(f"Found in {os.path.join(root, file)}")
search('c:/Users/GOWTHAMI/Downloads/projects/recruiting-platform/frontend')
