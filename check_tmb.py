import urllib.request, zipfile, io, csv, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
url = "https://api.tmb.cat/v1/static/datasets/gtfs.zip?app_id=f87364db&app_key=fb9898a5d8988e645bba1a6eaa956b65"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
raw = urllib.request.urlopen(req, timeout=600, context=ctx).read()
zf = zipfile.ZipFile(io.BytesIO(raw))
with zf.open("routes.txt") as f:
    for r in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
        if r.get("route_type") == "0":
            print(r.get("route_short_name"), r.get("route_color"))
