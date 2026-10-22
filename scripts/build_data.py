"""Turn Checkjebon's open price data into one compact file per supermarket, stores.json, per-store price history (from the repo's git history) and deals.json (clear price drops) for the Schapprijs app."""
import json, re, sys, subprocess, datetime

src, outdir = sys.argv[1], sys.argv[2]
repo = sys.argv[3] if len(sys.argv) > 3 else None

UNITS = {
    "g": ("kg", 0.001), "gr": ("kg", 0.001), "gram": ("kg", 0.001), "grm": ("kg", 0.001),
    "kg": ("kg", 1), "kilo": ("kg", 1),
    "ml": ("l", 0.001), "mililiters": ("l", 0.001), "milliliter": ("l", 0.001),
    "cl": ("l", 0.01), "l": ("l", 1), "liter": ("l", 1), "ltr": ("l", 1),
    "st": ("st", 1), "stuk": ("st", 1), "stuks": ("st", 1),
}
NUM = r"(\d+(?:[.,]\d+)?)"
MULTI = re.compile(NUM + r"\s*x\s*" + NUM + r"\s*(kg|kilo|gram|grm|gr|g|mililiters|milliliter|ml|cl|liter|ltr|l|stuks|stuk|st)\b", re.I)
SINGLE = re.compile(r"(?:ca\.?\s*)?" + NUM + r"\s*(kg|kilo|gram|grm|gr|g|mililiters|milliliter|ml|cl|liter|ltr|l|stuks|stuk|st)\b", re.I)


def num(s):
    return float(s.replace(",", "."))


def parse_size(text):
    if not text:
        return None
    m = MULTI.search(text)
    if m:
        kind, f = UNITS[m.group(3).lower()]
        return kind, num(m.group(1)) * num(m.group(2)) * f
    m = SINGLE.search(text)
    if m:
        kind, f = UNITS[m.group(2).lower()]
        return kind, num(m.group(1)) * f
    if re.search(r"\bper stuk\b", text, re.I):
        return "st", 1
    return None


import os
os.makedirs(outdir, exist_ok=True)
data = {s["n"]: s for s in json.load(open(src, encoding="utf-8"))}
result = {"stores": {}}
for key, s in data.items():
    rows = []
    seen = set()
    for p in s["d"]:
        name, price = (p.get("n") or "").strip(), p.get("p")
        name = re.sub(r"[\ufffd\x00-\x1f\x7f-\x9f]", "", name.replace("Nestl\ufffd", "Nestlé")).strip()
        if not name or not isinstance(price, (int, float)) or price <= 0:
            continue
        size = (p.get("s") or "").strip()
        sig = (name.lower(), size, price)
        if sig in seen:
            continue
        seen.add(sig)
        parsed = parse_size(size) or parse_size(name)
        unit_price, unit = None, ""
        if parsed and parsed[1] > 0:
            unit, qty = parsed
            unit_price = round(price / qty, 2)
            if unit_price > 2000:  # parse error guard
                unit_price, unit = None, ""
        rows.append([name, p.get("l", ""), round(price, 2), size, unit_price, unit])
    result["stores"][key] = {"base": s["u"], "items": rows, "label": s.get("c", key)}

stamp = None
if repo:
    try:
        stamp = subprocess.run(["git", "-C", repo, "log", "-1", "--format=%cI"],
                               capture_output=True, text=True).stdout.strip()
    except Exception:
        stamp = None
result["updated"] = stamp or datetime.datetime.now(datetime.timezone.utc).isoformat()

index = {"updated": result["updated"], "stores": {}}
for key, block in result["stores"].items():
    index["stores"][key] = {"label": block["label"], "count": len(block["items"])}
    if block["items"]:
        with open(os.path.join(outdir, f"prices-{key}.json"), "w", encoding="utf-8") as f:
            json.dump({"base": block["base"], "items": block["items"], "updated": result["updated"]}, f, ensure_ascii=False, separators=(",", ":"))
    print(key, len(block["items"]))
with open(os.path.join(outdir, "stores.json"), "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, separators=(",", ":"))


# ---- Price history and price drops, rebuilt each run from the daily snapshots in the repo's git history ----
DAYS = 30
history_days, history = [], {}  # history[store][rel_link] = [cents per day]
if repo:
    log = subprocess.run(["git", "-C", repo, "log", "--format=%H %cI", "--", "data/supermarkets.json"],
                         capture_output=True, text=True).stdout.split("\n")
    per_day = {}
    for line in log:
        if not line.strip():
            continue
        h, iso = line.split(" ", 1)
        day = iso[:10]
        per_day.setdefault(day, h)  # newest commit of each day (log is newest first)
    days = sorted(per_day)[-DAYS:]
    snaps = []
    for day in days:
        raw = subprocess.run(["git", "-C", repo, "show", per_day[day] + ":data/supermarkets.json"], capture_output=True).stdout
        try:
            snap = {st["n"]: {p.get("l", ""): p.get("p") for p in st["d"]} for st in json.loads(raw.decode("utf-8", "replace"))}
        except Exception:
            continue
        snaps.append((day, snap))
    history_days = [d for d, _ in snaps]
    for key, block in result["stores"].items():
        series = {}
        for row in block["items"]:
            rel = row[1]
            if rel in series:
                continue
            vals = []
            for _, snap in snaps:
                v = snap.get(key, {}).get(rel)
                vals.append(int(round(v * 100)) if isinstance(v, (int, float)) and v > 0 else 0)
            series[rel] = vals
        history[key] = series

deals = []
for key, series in history.items():
    names = {r[1]: r for r in result["stores"][key]["items"]}
    for rel, vals in series.items():
        if len(vals) < 2 or not vals[-1]:
            continue
        now = vals[-1]
        before = sorted(v for v in vals[:-1] if v)
        if len(before) < 7:
            continue
        usual = before[len(before) // 2]
        if now <= usual * 0.85 and usual - now >= 15:
            since_i = len(vals) - 1
            while since_i > 0 and vals[since_i - 1] and vals[since_i - 1] <= now * 1.02:
                since_i -= 1
            r = names[rel]
            deals.append({"s": key, "l": rel, "n": r[0], "z": r[3], "p": now, "u": usual, "lo": min(before + [now]),
                          "d": round(100 * (usual - now) / usual), "since": history_days[since_i], "h": vals})
deals.sort(key=lambda d: -d["d"])
with open(os.path.join(outdir, "deals.json"), "w", encoding="utf-8") as f:
    json.dump({"updated": result["updated"], "days": history_days, "deals": deals}, f, ensure_ascii=False, separators=(",", ":"))
for key, series in history.items():
    if series:
        with open(os.path.join(outdir, f"history-{key}.json"), "w", encoding="utf-8") as f:
            json.dump({"days": history_days, "p": series}, f, ensure_ascii=False, separators=(",", ":"))
print("history days:", len(history_days), "price drops:", len(deals))
