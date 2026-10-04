with open('scripts/build_shapes.py', 'r') as f:
    code = f.read()

code = code.replace("transport-bcn-build/1.0", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

with open('scripts/build_shapes.py', 'w') as f:
    f.write(code)
