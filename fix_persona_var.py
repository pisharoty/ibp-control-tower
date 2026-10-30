import py_compile

with open("main.py", "r") as f:
    code = f.read()

# Ensure persona variable exists in active module scope
persona_init = '\n# Ensure persona variable exists in active module scope\nif "persona" not in locals() and "persona" not in globals():\n    persona = st.session_state.get("persona", "Commercial Commodities & Trading")\n'

if "nav_val = " in code:
    pos = code.find("nav_val = ")
    line_start = code.rfind("\n", 0, pos)
    code = code[:line_start] + persona_init + code[line_start:]
elif "render_executive_sop(persona)" in code:
    pos = code.find("render_executive_sop(persona)")
    line_start = code.rfind("\n", 0, pos)
    code = code[:line_start] + persona_init + code[line_start:]

with open("main.py", "w") as f:
    f.write(code)

py_compile.compile("main.py", doraise=True)
print("✓ Successfully initialized persona variable in router scope!")
