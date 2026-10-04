import urllib.request, zipfile, io, csv, json, os

def fetch_gtfs(url):
    req = urllib.request.Request(url, headers={"User-Agent": "transport-bcn-build/1.0"})
    raw = urllib.request.urlopen(req, timeout=600).read()
    return zipfile.ZipFile(io.BytesIO(raw))

def get_fgc_gtfs():
    PORTAL = "https://dadesobertes.fgc.cat/api/explore/v2.1/catalog/datasets/gtfs_zip/records?limit=20"
    req = urllib.request.Request(PORTAL, headers={"User-Agent": "transport-bcn-build/1.0"})
    datos = json.loads(urllib.request.urlopen(req, timeout=120).read())
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for item in datos.get("results", []):
            f = item.get("file") or {}
            nombre = f.get("filename", "")
            if nombre in {"routes.txt", "trips.txt", "shapes.txt"}:
                with urllib.request.urlopen(urllib.request.Request(
                        f["url"], headers={"User-Agent": "transport-bcn-build/1.0"}), timeout=600) as fr:
                    z.writestr(nombre, fr.read())
    return zipfile.ZipFile(buf)

def extract_shapes(gtfs_source, out_dict, allowed_types=None, force_color=None):
    if isinstance(gtfs_source, str):
        print(f"Fetching {gtfs_source}...")
        try:
            zf = fetch_gtfs(gtfs_source)
        except Exception as e:
            print(f"Error: {e}")
            return
    else:
        zf = gtfs_source
        
    routes = {}
    with zf.open("routes.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
            rtype = (r.get("route_type") or "").strip()
            if allowed_types is None or rtype in allowed_types:
                # Si el short_name empieza por N o bus, saltar (solo queremos tren/tram)
                rname = (r.get("route_short_name") or r.get("route_long_name") or "").upper()
                if "BUS" in rname or rtype == "3":
                    continue
                color = r.get("route_color")
                if not color or color.lower() == "ffffff" or color == "000000":
                    color = force_color or "5f6670"
                routes[r["route_id"]] = color.upper()
                
    if not routes: return
    
    trip_shapes = {}
    trip_routes = {}
    with zf.open("trips.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
            if r["route_id"] in routes:
                shape_id = r.get("shape_id")
                if shape_id:
                    trip_shapes[shape_id] = r["route_id"]
                    if r["route_id"] not in trip_routes:
                        trip_routes[r["route_id"]] = set()
                    trip_routes[r["route_id"]].add(shape_id)
                    
    shapes_pts = {}
    if "shapes.txt" in zf.namelist():
        with zf.open("shapes.txt") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
                sid = r["shape_id"]
                if sid in trip_shapes:
                    if sid not in shapes_pts: shapes_pts[sid] = []
                    shapes_pts[sid].append((int(r["shape_pt_sequence"]), float(r["shape_pt_lat"]), float(r["shape_pt_lon"])))
                    
    for rid, sids in trip_routes.items():
        # Tomar el shape con más puntos (recorrido completo)
        best_sid = max(sids, key=lambda sid: len(shapes_pts.get(sid, []))) if sids else None
        if best_sid and best_sid in shapes_pts:
            pts = sorted(shapes_pts[best_sid])
            # BBOX para recortar a Barcelona y alrededores
            pts = [(lat, lon) for _, lat, lon in pts if 41.0 < lat < 42.4 and 1.2 < lon < 2.6]
            if not pts: continue
            simplified = [[round(lat, 5), round(lon, 5)] for lat, lon in pts[::2]] # downsample 2x
            out_dict[rid] = {"c": routes[rid], "p": simplified}

def main():
    tmb_url = "https://api.tmb.cat/v1/static/datasets/gtfs.zip?app_id=f87364db&app_key=fb9898a5d8988e645bba1a6eaa956b65"
    renfe_url = "https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip"
    tram_url = "https://opendata.tram.cat/GTFS/TRAM_GTFS.zip"
    
    shapes = {}
    extract_shapes(tmb_url, shapes, {"1"}, "E20613") # Metro TMB
    print("Fetching FGC...")
    try:
        fgc_zf = get_fgc_gtfs()
        extract_shapes(fgc_zf, shapes, {"2"}, "000000") # FGC
    except Exception as e:
        print("FGC error:", e)
    extract_shapes(renfe_url, shapes, {"2"}, "EF3340") # Rodalies
    extract_shapes(tram_url, shapes, {"0"}, "008F4C") # TRAM
    
    with open("shapes.json", "w", encoding="utf-8") as f:
        json.dump(shapes, f, separators=(",", ":"))
    print(f"Saved {len(shapes)} shapes.")

if __name__ == "__main__":
    main()
