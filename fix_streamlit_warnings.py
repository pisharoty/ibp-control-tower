import os
import re

files_to_fix = [f for f in ["main.py", "robot_feeds.py"] if os.path.exists(f)]

for filename in files_to_fix:
    with open(filename, "r") as f:
        code = f.read()

    # Replace legacy Streamlit container parameters with new syntax
    updated_code = re.sub(r'use_container_width\s*=\s*True', "width='stretch'", code)
    updated_code = re.sub(r'use_container_width\s*=\s*False', "width='content'", updated_code)

    if updated_code != code:
        with open(filename, "w") as f:
            f.write(updated_code)
        print(f"✅ Updated container width parameters in {filename}.")
    else:
        print(f"ℹ️ No legacy parameters found in {filename}.")
