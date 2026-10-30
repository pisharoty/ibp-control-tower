import os
import re

targets = [f for f in ["robot_feeds.py", "robot_feeds.txt"] if os.path.exists(f)]

for target in targets:
    with open(target, "r") as f:
        code = f.read()

    # Replace any broken FRED split line with .splitlines()
    code = re.sub(
        r'lines\s*=\s*\[line for line in res\.text\.strip\(\)\.split[\s\S]*?\]',
        'lines = [line for line in res.text.strip().splitlines() if line and not line.startswith("DATE")]',
        code
    )

    with open(target, "w") as f:
        f.write(code)
    print(f"✅ Fixed syntax error in {target}.")
