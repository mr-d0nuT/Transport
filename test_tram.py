import urllib.request, zipfile, io, csv, json

def fetch_gtfs(url):
    req = urllib.request.Request(url, headers={"User-Agent": "transport-bcn-build/1.0"})
    raw = urllib.request.urlopen(req, timeout=600).read()
    return zipfile.ZipFile(io.BytesIO(raw))

tram_url = "https://opendata.tram.cat/GTFS/TRAM_GTFS.zip"
try:
    zf = fetch_gtfs(tram_url)
    print("Files:", zf.namelist())
    routes = []
    with zf.open("routes.txt") as f:
        for r_raw in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
            routes.append(r_raw)
    print("Routes:", routes)
except Exception as e:
    print("Error:", e)
