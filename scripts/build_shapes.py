import urllib.request, zipfile, io, csv, json

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
                with urllib.request.urlopen(urllib.request.Request(f["url"], headers={"User-Agent": "transport-bcn-build/1.0"}), timeout=600) as fr:
                    z.writestr(nombre, fr.read())
    return zipfile.ZipFile(buf)

def clean_dict(d):
    return {k.strip(): v.strip() for k, v in d.items() if k and v}

global_idx = 0

def extract_shapes(gtfs_source, out_dict, allowed_types=None, force_color=None, downsample=2):
    global global_idx
    if isinstance(gtfs_source, str):
        try:
            zf = fetch_gtfs(gtfs_source)
        except Exception as e:
            return
    else:
        zf = gtfs_source
        
    routes = {}
    with zf.open("routes.txt") as f:
        for r_raw in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
            r = clean_dict(r_raw)
            rtype = r.get("route_type", "")
            if allowed_types is None or rtype in allowed_types:
                color = r.get("route_color")
                if not color or color.lower() == "ffffff" or color == "000000":
                    color = force_color or "5f6670"
                routes[r["route_id"]] = (color.upper(), rtype)
                
    if not routes: return
    
    trip_shapes = {}
    trip_routes = {}
    with zf.open("trips.txt") as f:
        for r_raw in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
            r = clean_dict(r_raw)
            if r.get("route_id") in routes:
                shape_id = r.get("shape_id")
                direction = r.get("direction_id", "0")
                if shape_id:
                    route_dir = f"{r['route_id']}_{direction}"
                    trip_shapes[shape_id] = route_dir
                    if route_dir not in trip_routes:
                        trip_routes[route_dir] = set()
                    trip_routes[route_dir].add(shape_id)
                    
    shapes_pts = {}
    if "shapes.txt" in zf.namelist():
        with zf.open("shapes.txt") as f:
            for r_raw in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
                r = clean_dict(r_raw)
                sid = r.get("shape_id")
                if sid in trip_shapes:
                    if sid not in shapes_pts: shapes_pts[sid] = []
                    shapes_pts[sid].append((int(r["shape_pt_sequence"]), float(r.get("shape_pt_lat", 0)), float(r.get("shape_pt_lon", 0))))
                    
    for route_dir, sids in trip_routes.items():
        rid = route_dir.split("_")[0]
        best_sid = max(sids, key=lambda sid: len(shapes_pts.get(sid, []))) if sids else None
        if best_sid and best_sid in shapes_pts:
            pts = sorted(shapes_pts[best_sid])
            pts = [(lat, lon) for _, lat, lon in pts if 40.5 < lat < 43.0 and 0.1 < lon < 3.5]
            if not pts: continue
            
            simplified = [[round(lat, 5), round(lon, 5)] for lat, lon in pts[::downsample]] 
            
            offset_px = ((global_idx % 7) - 3) * 3 
            global_idx += 1
            
            color, rtype = routes[rid]
            out_dict[route_dir] = {"c": color, "t": rtype, "p": simplified, "o": offset_px}

def main():
    tmb_url = "https://api.tmb.cat/v1/static/datasets/gtfs.zip?app_id=f87364db&app_key=fb9898a5d8988e645bba1a6eaa956b65"
    renfe_url = "https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip"
    tram_url = "https://opendata.tram.cat/GTFS/TRAM_GTFS.zip"
    amb_url = "https://www.ambmobilitat.cat/OpenData/google_transit.zip"
    gen_url = "https://analisi.transparenciacatalunya.cat/download/bca2-b4i3/application/zip"
    
    shapes = {}
    extract_shapes(tmb_url, shapes, {"1", "3"}, "E20613", downsample=2)
    extract_shapes(amb_url, shapes, {"3"}, "FFD700", downsample=3)
    extract_shapes(gen_url, shapes, {"3"}, "5f6670", downsample=5)
    try:
        fgc_zf = get_fgc_gtfs()
        extract_shapes(fgc_zf, shapes, {"2"}, "000000", downsample=2)
    except:
        pass
    extract_shapes(renfe_url, shapes, {"2"}, "EF3340", downsample=2)
    try:
        extract_shapes(tram_url, shapes, {"0"}, "008F4C", downsample=2)
    except:
        pass
        
    with open("shapes.json", "w", encoding="utf-8") as f:
        json.dump(shapes, f, separators=(",", ":"))

if __name__ == "__main__":
    main()
