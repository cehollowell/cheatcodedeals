#!/usr/bin/env python3
"""afflink.py - convert store URLs into affiliate links (no deps, no AI).
Usage: afflink.py <url>... [--json] | --check   (config: config.json beside script)"""
import json, os, sys
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode, quote

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.environ.get("AFFLINK_CONFIG", os.path.join(HERE, "config.json"))
# store -> (domains, mode, param)   mode: param = add query param; template = network deep link
STORES = {
    "amazon":     (["amazon.com", "amzn.to", "amzn.com"], "param", "tag"),
    "humble":     (["humblebundle.com"], "param", "partner"),
    "fanatical":  (["fanatical.com"], "template", None),
    "greenman":   (["greenmangaming.com"], "template", None),
    "bestbuy":    (["bestbuy.com"], "template", None),
    "walmart":    (["walmart.com"], "template", None),
    "target":     (["target.com"], "template", None),
    "gamestop":   (["gamestop.com"], "template", None),
}
NO_PROGRAM = {"store.steampowered.com": "Steam", "store.playstation.com": "PlayStation Store",
              "nintendo.com": "Nintendo eShop", "xbox.com": "Xbox Store"}
TRACKING = {"tag", "ascsubtag", "linkcode", "linkid", "camp", "creative", "creativeasin", "ref_",
            "ref", "pf_rd_r", "pf_rd_p", "pd_rd_r", "pd_rd_w", "pd_rd_wg", "psc", "th", "smid",
            "content-id", "partner", "irgwc", "irclickid", "clickid", "sharedid", "subid", "subid1",
            "subid2", "subid3", "cjevent", "cjdata", "aid", "pid", "affid", "affiliate", "afsrc",
            "veh", "wmlspartner", "sourceid", "adid", "gclid", "fbclid", "ttclid", "twclid", "msclkid",
            "dclid", "snr", "smcid", "afid", "clkid", "affiliates_ad_id", "keywords", "sr", "qid", "crid", "sprefix", "mc_cid", "mc_eid", "igshid", "si", "s", "ranmid", "raneaid", "ransiteid", "u1"}

def load_cfg():
    try:
        with open(CFG) as f: return json.load(f)
    except FileNotFoundError: return {}

def find_store(host):
    host = host.lower().split(":")[0]
    for name, (doms, _, _) in STORES.items():
        if any(host == d or host.endswith("." + d) for d in doms): return name
    for d, label in NO_PROGRAM.items():
        if host == d or host.endswith("." + d): return "none:" + label
    return None

def clean(u):
    p = urlsplit(u.strip())
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
         if k.lower() not in TRACKING and not k.lower().startswith(("utm_", "pf_rd", "pd_rd", "irclick"))]
    path = p.path
    if "amazon." in p.netloc:  # drop /ref=... path segment
        i = path.find("/ref=")
        if i != -1: path = path[:i]
    return urlunsplit((p.scheme or "https", p.netloc, path, urlencode(q), ""))

def convert(url, cfg):
    store = find_store(urlsplit(url.strip()).netloc)
    c = clean(url)
    if store is None: return c, None, "unknown store; returned cleaned URL"
    if store.startswith("none:"): return c, store[5:], "no general affiliate program; returned cleaned URL"
    sc = cfg.get(store, {}) or {}
    _, mode, param = STORES[store]
    tmpl = (sc.get("template") or "").strip()
    if tmpl:  # template overrides, e.g. https://x.sjv.io/c/123/456/789?u={url_enc}
        return tmpl.replace("{url_enc}", quote(c, safe="")).replace("{url}", c), store, None
    if mode == "param" and (sc.get("id") or "").strip():
        p = urlsplit(c); q = parse_qsl(p.query, keep_blank_values=True) + [(param, sc["id"].strip())]
        return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), "")), store, None
    return c, store, "not configured (fill config.json); returned cleaned URL"

def main(a):
    as_json = "--json" in a; urls = [x for x in a if not x.startswith("--")]
    cfg = load_cfg()
    if "--check" in a:
        for s, (_, mode, _) in STORES.items():
            sc = cfg.get(s, {}) or {}
            ok = bool((sc.get("template") or "").strip() or (mode == "param" and (sc.get("id") or "").strip()))
            print(f"{s:10} {'CONFIGURED' if ok else 'missing':10} ({'id or template' if mode=='param' else 'template'})")
        print("no program: " + ", ".join(NO_PROGRAM.values())); return 0
    if not urls: print(__doc__, file=sys.stderr); return 2
    out = []
    for u in urls:
        link, store, warn = convert(u, cfg)
        if warn: print(f"warning: {store or '?'}: {warn}: {u}", file=sys.stderr)
        out.append({"input": u, "store": store, "link": link, "affiliate": warn is None, "warning": warn})
    if as_json: print(json.dumps(out, indent=2))
    else: print("\n".join(o["link"] for o in out))
    return 0

if __name__ == "__main__": sys.exit(main(sys.argv[1:]))
