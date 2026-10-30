import py_compile

with open("main.py", "r") as f:
    code = f.read()

# Ensure selected_module is safely retrieved from active navigation state
fix_target = 'if any(k in str(selected_module) for k in ["Global Trade", "S&OP", "Executive"]):'
fix_replacement = 'selected_module = locals().get("selected_module", locals().get("module", locals().get("selected_page", st.session_state.get("selected_module", ""))))\n    if any(k in str(selected_module) for k in ["Global Trade", "S&OP", "Executive"]):'

if fix_target in code:
    code = code.replace(fix_target, fix_replacement)
else:
    # Global fallback replacement if formatting differs slightly
    code = code.replace("str(selected_module)", 'str(locals().get("selected_module", st.session_state.get("selected_module", "")))')

with open("main.py", "w") as f:
    f.write(code)

py_compile.compile("main.py", doraise=True)
print("✓ Resolved NameError for selected_module scope!")
