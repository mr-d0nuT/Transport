import urllib.request, zipfile, io, csv

def test_size(url, allowed_types):
    print(f"Fetching {url}")
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "test/1.0"}), timeout=60).read()
    except Exception as e:
        print(f"Error {e}")
        return
    zf = zipfile.ZipFile(io.BytesIO(raw))
    
    trip_shapes = set()
    with zf.open("routes.txt") as f:
        routes = set(r["route_id"] for r in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")) if r.get("route_type") in allowed_types)
    with zf.open("trips.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
            if r["route_id"] in routes and r.get("shape_id"):
                trip_shapes.add(r["shape_id"])
    
    pts = 0
    if "shapes.txt" in zf.namelist():
        with zf.open("shapes.txt") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
                if r["shape_id"] in trip_shapes:
                    pts += 1
    print(f"URL: {url} -> {len(routes)} routes, {len(trip_shapes)} shapes, {pts} points")

test_size("https://www.ambmobilitat.cat/OpenData/google_transit.zip", {"3"})
test_size("https://analisi.transparenciacatalunya.cat/download/bca2-b4i3/application/zip", {"3"})
