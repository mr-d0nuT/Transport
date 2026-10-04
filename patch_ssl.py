import ssl
def build_patch():
    with open('scripts/build_shapes.py', 'r') as f:
        code = f.read()
    
    ssl_patch = """
import urllib.request, zipfile, io, csv, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
"""
    code = code.replace("import urllib.request, zipfile, io, csv, json", ssl_patch)
    code = code.replace("urllib.request.urlopen(req, timeout=600)", "urllib.request.urlopen(req, timeout=600, context=ctx)")
    code = code.replace("urllib.request.urlopen(req, timeout=120)", "urllib.request.urlopen(req, timeout=120, context=ctx)")
    code = code.replace("urllib.request.urlopen(urllib.request.Request(f[\"url\"], headers={\"User-Agent\": \"transport-bcn-build/1.0\"}), timeout=600)", "urllib.request.urlopen(urllib.request.Request(f[\"url\"], headers={\"User-Agent\": \"transport-bcn-build/1.0\"}), timeout=600, context=ctx)")
    
    with open('scripts/build_shapes.py', 'w') as f:
        f.write(code)

build_patch()
