import os
import re

targets = [f for f in ["robot_feeds.py", "robot_feeds.txt"] if os.path.exists(f)]

for target in targets:
    with open(target, "r") as f:
        code = f.read()

    # Remove any misplaced import or ensure it leads at line 1
    code = re.sub(r"^import streamlit as st\n?", "", code, flags=re.MULTILINE)
    code = "import streamlit as st\n" + code

    with open(target, "w") as f:
        f.write(code)
    print(f"✅ Fixed Streamlit import order in {target}.")
