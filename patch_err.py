with open('scripts/build_shapes.py', 'r') as f:
    code = f.read()

code = code.replace("except:\n        pass", "except Exception as e:\n        print('ERROR:', e)")

with open('scripts/build_shapes.py', 'w') as f:
    f.write(code)
