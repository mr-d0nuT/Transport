import urllib.request, zipfile, io, csv, json, os, math

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

def clean_dict(d):
    return {k.strip(): v.strip() for k, v in d.items() if k and v}

def offset_polyline(points, offset_meters):
    if len(points) < 2 or offset_meters == 0: return points
    offset_pts = []
    for i in range(len(points)):
        if i == 0:
            p1, p2 = points[0], points[1]
        elif i == len(points) - 1:
            p1, p2 = points[-2], points[-1]
        else:
            p1, p2 = points[i-1], points[i+1]
        lat1, lon1 = p1
        lat2, lon2 = p2
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        plon = -dlat
        plat = dlon
        length = math.hypot(plat, plon)
        if length == 0:
            offset_pts.append(points[i])
            continue
        lat_offset = (plat / length) * (offset_meters / 111320.0)
        lon_offset = (plon / length) * (offset_meters / (111320.0 * math.cos(math.radians(points[i][0]))))
        offset_pts.append((points[i][0] + lat_offset, points[i][1] + lon_offset))
    return offset_pts

global_idx = 0

def extract_shapes(gtfs_source, out_dict, allowed_types=None, force_color=None):
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
        for r_raw in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
            r = clean_dict(r_raw)
            if r.get("route_id") in routes:
                shape_id = r.get("shape_id")
                if shape_id:
                    trip_shapes[shape_id] = r["route_id"]
                    if r["route_id"] not in trip_routes:
                        trip_routes[r["route_id"]] = set()
                    trip_routes[r["route_id"]].add(shape_id)
                    
    shapes_pts = {}
    if "shapes.txt" in zf.namelist():
        with zf.open("shapes.txt") as f:
            for r_raw in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
                r = clean_dict(r_raw)
                sid = r.get("shape_id")
                if sid in trip_shapes:
                    if sid not in shapes_pts: shapes_pts[sid] = []
                    shapes_pts[sid].append((int(r["shape_pt_sequence"]), float(r.get("shape_pt_lat", 0)), float(r.get("shape_pt_lon", 0))))
                    
    for rid, sids in trip_routes.items():
        best_sid = max(sids, key=lambda sid: len(shapes_pts.get(sid, []))) if sids else None
        if best_sid and best_sid in shapes_pts:
            pts = sorted(shapes_pts[best_sid])
            pts = [(lat, lon) for _, lat, lon in pts if 40.5 < lat < 43.0 and 0.1 < lon < 3.5]
            if not pts: continue
            # Calculate offset: alternate left and right by 15 meters
            offset = ((global_idx % 7) - 3) * 20 # -60, -40, -20, 0, 20, 40, 60 meters
            global_idx += 1
            pts_offset = offset_polyline(pts, offset)
            
            simplified = [[round(lat, 5), round(lon, 5)] for lat, lon in pts_offset[::2]] # downsample 2x
            out_dict[rid] = {"c": routes[rid], "p": simplified}

def main():
    tmb_url = "https://api.tmb.cat/v1/static/datasets/gtfs.zip?app_id=f87364db&app_key=fb9898a5d8988e645bba1a6eaa956b65"
    renfe_url = "https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip"
    
    shapes = {}
    extract_shapes(tmb_url, shapes, {"1"}, "E20613") # Metro TMB
    try:
        fgc_zf = get_fgc_gtfs()
        extract_shapes(fgc_zf, shapes, {"2"}, "000000") # FGC
    except:
        pass
    extract_shapes(renfe_url, shapes, {"2"}, "EF3340") # Rodalies
    
    with open("shapes.json", "w", encoding="utf-8") as f:
        json.dump(shapes, f, separators=(",", ":"))

if __name__ == "__main__":
    main()
