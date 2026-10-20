#!/usr/bin/env python3
"""Build CheatCodeDeals static site: posts/*.md -> site/.  Usage: python3 build.py [--drafts]
SITE_URL env (or config below) must be the final https URL for OG/RSS/sitemap absolute links."""
import os, re, sys, json, html, shutil, subprocess, datetime as dt
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
ROOT=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(ROOT,"site")
SITE_URL=os.environ.get("SITE_URL","https://cheatcodedeals.example.com").rstrip("/")
# Project Pages lives under a subpath (e.g. /cheatcodedeals). Root-absolute
# links (/style.css, /img/...) must include that path or the browser requests
# them from the domain root.
BASE=urlsplit(SITE_URL).path.rstrip("/")
def urlpath(p):
    if not p.startswith("/"): p="/"+p
    return BASE+p
NAME="CheatCodeDeals"; X="CheatCodeDeals"; ET=ZoneInfo("America/New_York")
CATS=["Games","Electronics","Collectibles & Pokemon","Drops & Announcements"]
AFF=os.path.join(ROOT,"tools","afflink.py")
DISCLOSURE="Some links may be affiliate links. If you buy through them we may earn a small commission at no extra cost to you. It never decides which deals we post."
NOW=dt.datetime.fromisoformat(os.environ["BUILD_NOW"]).replace(tzinfo=ET) if os.environ.get("BUILD_NOW") else dt.datetime.now(ET)
esc=html.escape
def slugify(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")

def aff(urls):
    if not urls or not os.path.exists(AFF): return {u:u for u in urls}
    try:
        r=subprocess.run([sys.executable,AFF,*urls,"--json"],capture_output=True,text=True,timeout=30)
        return {x["input"]:x.get("link") or x["input"] for x in json.loads(r.stdout)}
    except Exception as e:
        print("warning: afflink failed:",e,file=sys.stderr); return {u:u for u in urls}

def parse(path):
    t=open(path,encoding="utf-8").read(); m=re.match(r"---\n(.*?)\n---\n(.*)",t,re.S)
    if not m: raise SystemExit(f"{path}: missing front matter")
    fm={}
    for ln in m.group(1).splitlines():
        if ":" in ln: k,v=ln.split(":",1); fm[k.strip()]=v.strip()
    fm["body"]=m.group(2).strip(); fm["slug"]=fm.get("slug") or re.sub(r"\.md$","",os.path.basename(path))
    fm["dt"]=dt.datetime.fromisoformat(fm["date"].replace(" ","T")).replace(tzinfo=ET)
    e=fm.get("ends","")
    if e:
        ed=dt.datetime.fromisoformat(e)
        if "T" not in e: ed=ed.replace(hour=23,minute=59)   # date-only = end of day ET
        fm["end_dt"]=ed.replace(tzinfo=ET)
    else: fm["end_dt"]=None
    fm["expired"]=bool(fm["end_dt"] and NOW>fm["end_dt"])
    if fm.get("category") not in CATS: raise SystemExit(f"{path}: category must be one of {CATS}")
    return fm

def md(s, links):
    out=[]
    for para in re.split(r"\n\s*\n",s):
        p=esc(para.strip())
        p=re.sub(r"\*\*(.+?)\*\*",r"<strong>\1</strong>",p)
        p=re.sub(r"\[(.+?)\]\((https?://[^)]+)\)",lambda m:f'<a href="{esc(links.get(html.unescape(m[2]),html.unescape(m[2])))}" rel="nofollow sponsored noopener">{m[1]}</a>',p)
        if p: out.append(f"<p>{p.replace(chr(10),'<br>')}</p>")
    return "\n".join(out)

def enddisp(p):
    e=p["end_dt"]
    if not e: return ""
    s=f"{e:%b} {e.day}"
    if p["ends"].count("T"): s+=f", {e.strftime('%I:%M %p').lstrip('0')} ET"
    return s

CSS="""
:root{--y:#ffd600;--r:#eb283c;--bg:#08080e;--card:#14141d;--mut:#a9a9b8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#fff;font:17px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:var(--y)}header{border-top:6px solid var(--y);background:#0e0e16;position:sticky;top:0;z-index:5}
.wrap{max-width:1180px;margin:0 auto;padding:0 18px}.nav{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding:14px 18px}
.logo{font:900 26px/1 Impact,'Arial Narrow Bold',sans-serif;letter-spacing:.5px;color:#fff;text-decoration:none;text-transform:uppercase}.logo b{color:var(--y)}
.nav a.l{color:#fff;text-decoration:none;font-weight:700;font-size:15px}.nav a.l:hover{color:var(--y)}.sp{flex:1}
h1,h2,h3{font-family:Impact,'Arial Narrow Bold',sans-serif;font-weight:900;text-transform:uppercase;letter-spacing:.3px;line-height:1.1}
.hero{padding:34px 0 10px}.hero h1{font-size:44px;margin:0}.hero p{color:var(--mut);margin:6px 0 0}
.tags{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}.tag{border:2px solid #333;border-radius:999px;padding:4px 12px;font-size:14px;font-weight:700;color:#fff;text-decoration:none}.tag:hover,.tag.on{border-color:var(--y);color:var(--y)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:22px;padding:10px 0 40px}
.card{background:var(--card);border-radius:14px;overflow:hidden;border:1px solid #23232f;display:flex;flex-direction:column;position:relative;text-decoration:none;color:#fff;transition:transform .15s}
.card:hover{transform:translateY(-3px);border-color:var(--y)}.card img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}
.card .b{padding:14px 16px 16px}.card h3{margin:0 0 8px;font-size:22px}
.price{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}.now{font:900 34px/1 Impact,sans-serif;color:var(--y)}.was{color:var(--mut);text-decoration:line-through;text-decoration-color:var(--r);text-decoration-thickness:3px}
.off{background:var(--r);color:#fff;font-weight:900;border-radius:7px;padding:2px 8px}
.meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;font-size:14px}.pill{border:2px solid #fff;border-radius:7px;padding:1px 8px;font-weight:700}.ends{color:var(--y);font-weight:700}
.status{background:var(--y);color:#000;font-weight:900;font-size:13px;border-radius:6px;padding:2px 8px;text-transform:uppercase}
.exp{opacity:.55}.exp img{filter:grayscale(1)}.xlabel{position:absolute;top:14px;left:14px;background:#000;color:#fff;border:2px solid var(--r);font-weight:900;padding:3px 10px;border-radius:6px;text-transform:uppercase;letter-spacing:1px;z-index:2}
article{max-width:860px;margin:0 auto;padding:28px 0 40px}article img.g{width:100%;border-radius:12px;border:3px solid var(--y)}article h1{font-size:40px;margin:18px 0 10px}
.buy{display:inline-block;background:var(--y);color:#000;font-weight:900;text-decoration:none;padding:14px 26px;border-radius:10px;margin:18px 0;text-transform:uppercase}.buy.dead{background:#333;color:#aaa}
.note{color:var(--mut);font-size:14px}.prose{max-width:760px;padding:30px 0 50px}
footer{border-top:1px solid #222;color:var(--mut);font-size:14px;padding:24px 0 40px}footer a{color:#fff}
@media(max-width:600px){header{position:static}.nav a.c{display:none}.hero h1{font-size:32px}article h1{font-size:30px}.grid{grid-template-columns:1fr}}
"""

def page(title,body,desc="",og_img=None,url="/",typ="website"):
    full=SITE_URL+url; img=SITE_URL+og_img if og_img else SITE_URL+"/img/og-default.png"
    d=esc(desc or "Real game deals, every price verified live before posting.")
    nav="".join(f'<a class="l c" href="{urlpath("/category/"+slugify(c)+"/")}">{esc(c)}</a>' for c in CATS)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{d}"><link rel="canonical" href="{full}">
<meta property="og:type" content="{typ}"><meta property="og:site_name" content="{NAME}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{d}"><meta property="og:url" content="{full}">
<meta property="og:image" content="{img}"><meta property="og:image:width" content="1600"><meta property="og:image:height" content="900">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:site" content="@{X}"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{d}"><meta name="twitter:image" content="{img}">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="{urlpath("/feed.xml")}"><link rel="stylesheet" href="{urlpath("/style.css")}"></head><body>
<header><div class="wrap nav"><a class="logo" href="{urlpath("/")}">Cheat<b>Code</b>Deals</a>{nav}<span class="sp"></span><a class="l" href="{urlpath("/about/")}">About</a><a class="l" href="https://x.com/{X}">@{X}</a></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap">{esc(DISCLOSURE)} <a href="{urlpath("/disclosure/")}">Affiliate disclosure</a> · <a href="{urlpath("/about/")}">How we verify prices</a> · <a href="{urlpath("/feed.xml")}">RSS</a><br>Prices can change without warning, so check the store before you buy. © {NOW.year} {NAME}</div></footer></body></html>"""

def card(p):
    e=" exp" if p["expired"] else ""
    xl='<span class="xlabel">Expired</span>' if p["expired"] else ""
    was=f'<span class="was">{esc(p["was"])}</span>' if p.get("was") else ""
    off=f'<span class="off">-{esc(p["off"])}</span>' if p.get("off") else ""
    st=f'<span class="status">{esc(p["status"])}</span>' if p.get("status") and not p["expired"] else ""
    ends=f'<span class="ends">{"Ended" if p["expired"] else "Ends"} {enddisp(p)}</span>' if p["end_dt"] else ""
    return f"""<a class="card{e}" href="{urlpath('/deals/'+p['slug']+'/')}">{xl}<img src="{urlpath(p['image'])}" alt="{esc(p['title'])} deal graphic" loading="lazy">
<div class="b"><h3>{esc(p['title'])}</h3><div class="price"><span class="now">{esc(p['price'])}</span>{was}{off}</div>
<div class="meta"><span class="pill">{esc(p['platform'])}</span>{ends}{st}</div></div></a>"""

def write(rel,s):
    path=os.path.join(OUT,rel.lstrip("/")); os.makedirs(os.path.dirname(path),exist_ok=True)
    open(path,"w",encoding="utf-8").write(s)

def main():
    drafts="--drafts" in sys.argv
    posts=[parse(os.path.join(ROOT,"posts",f)) for f in sorted(os.listdir(os.path.join(ROOT,"posts"))) if f.endswith(".md")]
    skipped=[p["slug"] for p in posts if p["dt"]>NOW and not drafts]
    posts=sorted([p for p in posts if drafts or p["dt"]<=NOW],key=lambda p:p["dt"],reverse=True)
    urls=set()
    for p in posts: urls.add(p["link"]); urls.update(re.findall(r"\]\((https?://[^)]+)\)",p["body"]))
    L=aff(sorted(urls))
    shutil.rmtree(OUT,ignore_errors=True); shutil.copytree(os.path.join(ROOT,"static"),OUT)
    write("style.css",CSS); write(".nojekyll","")
    tagbar=lambda on="":'<div class="tags"><a class="tag'+(" on" if not on else "")+f'" href="{urlpath("/")}">All</a>'+"".join(f'<a class="tag{" on" if c==on else ""}" href="{urlpath("/category/"+slugify(c)+"/")}">{esc(c)}</a>' for c in CATS)+"</div>"
    live=[p for p in posts if not p["expired"]]+[p for p in posts if p["expired"]]  # newest first, expired sink
    write("index.html",page(f"{NAME}: Verified Game Deals",f'<section class="hero"><h1>Today\'s <span style="color:var(--y)">verified</span> deals</h1><p>Every price checked live before we post. Newest first.</p></section>{tagbar()}<div class="grid">{"".join(card(p) for p in live)}</div>'))
    for c in CATS:
        cp=[p for p in live if p["category"]==c]
        g="".join(card(p) for p in cp) or '<p class="note">No posts here yet.</p>'
        write(f"category/{slugify(c)}/index.html",page(f"{c} · {NAME}",f'<section class="hero"><h1>{esc(c)}</h1></section>{tagbar(c)}<div class="grid">{g}</div>',url=f"/category/{slugify(c)}/"))
    for p in posts:
        link=L.get(p["link"],p["link"]); deal=bool(p.get("off"))
        desc=f'{p["price"]}'+(f' (was {p["was"]}, -{p["off"]})' if deal else "")+f' on {p["store"]}. '+(f'Ends {enddisp(p)}.' if p["end_dt"] else "")
        if p["expired"]: desc="EXPIRED: "+desc
        btn=f'<a class="buy dead" href="{esc(link)}" rel="nofollow sponsored noopener">Sale ended. Check current price</a>' if p["expired"] else f'<a class="buy" href="{esc(link)}" rel="nofollow sponsored noopener">Get it at {esc(p["store"])} →</a>'
        exp='<p><span class="xlabel" style="position:static">Expired</span> This sale has ended. The price shown was correct when we posted it.</p>' if p["expired"] else ""
        st=f' <span class="status">{esc(p["status"])}</span>' if p.get("status") else ""
        body=f"""<article><img class="g" src="{urlpath(p['image'])}" alt="{esc(p['title'])} deal graphic">{exp}
<h1>{esc(p['title'])}</h1><div class="price"><span class="now">{esc(p['price'])}</span>{f'<span class="was">{esc(p["was"])}</span>' if p.get("was") else ""}{f'<span class="off">-{esc(p["off"])}</span>' if deal else ""}</div>
<div class="meta"><span class="pill">{esc(p['platform'])}</span><span class="pill">{esc(p['store'])}</span>{f'<span class="ends">{"Ended" if p["expired"] else "Ends"} {enddisp(p)}</span>' if p["end_dt"] else ""}{st}</div>
{md(p['body'],L)}{btn}<p class="note">Posted {p['dt']:%b} {p['dt'].day}, {p['dt'].year} · Category: <a href="{urlpath('/category/'+slugify(p['category'])+'/')}">{esc(p['category'])}</a> · {esc(DISCLOSURE)}</p></article>"""
        write(f"deals/{p['slug']}/index.html",page(f"{p['title']}: {p['price']} · {NAME}",body,desc,p["image"],f"/deals/{p['slug']}/","article"))
    write("about/index.html",page(f"About · {NAME}",f"""<div class="prose"><h1>About {NAME}</h1>
<p><strong>Every price is verified live before posting.</strong> Before a deal goes up, we check the price on the store itself or a live price tracker that same day. If we can't confirm it, we don't post it.</p>
<p>We tell you whether it's a real all-time low ("Lowest price ever"), the best price yet, or just a solid discount. Every deal shows the sale price, the normal price, the % off, the platform and the end date.</p>
<p>Once a sale's end date passes, the deal is marked <strong>Expired</strong> so you never chase an old price.</p>
<p>Follow along on X: <a href="https://x.com/{X}">@{X}</a>. RSS: <a href="{urlpath('/feed.xml')}">{urlpath('/feed.xml')}</a>.</p></div>""",url="/about/"))
    write("disclosure/index.html",page(f"Affiliate Disclosure · {NAME}",f"""<div class="prose"><h1>Affiliate Disclosure</h1><p>{esc(DISCLOSURE)}</p>
<p>Links on this site go straight to the store. Where we're part of a retailer's affiliate program, the link may carry an affiliate tag. Many digital stores (PlayStation Store, Xbox, Nintendo eShop, Steam) have no general affiliate program, so those links earn us nothing.</p>
<p>Affiliate relationships never affect which deals we post or how we describe them.</p></div>""",url="/disclosure/"))
    items="".join(f"<item><title>{esc(p['title'])}: {esc(p['price'])}{' (EXPIRED)' if p['expired'] else ''}</title><link>{SITE_URL}/deals/{p['slug']}/</link><guid>{SITE_URL}/deals/{p['slug']}/</guid><pubDate>{p['dt'].strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate><category>{esc(p['category'])}</category><description>{esc(p['body'][:300])}</description><enclosure url=\"{SITE_URL}{p['image']}\" type=\"image/png\" length=\"0\"/></item>" for p in posts[:50])
    write("feed.xml",f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{NAME}</title><link>{SITE_URL}/</link><description>Verified game deals</description><lastBuildDate>{NOW.strftime("%a, %d %b %Y %H:%M:%S %z")}</lastBuildDate>{items}</channel></rss>')
    locs=["/","/about/","/disclosure/"]+[f"/category/{slugify(c)}/" for c in CATS]+[f"/deals/{p['slug']}/" for p in posts]
    write("sitemap.xml",'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+"".join(f"<url><loc>{SITE_URL}{u}</loc></url>" for u in locs)+"</urlset>")
    write("robots.txt",f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    write("404.html",page(f"Not found · {NAME}",f'<div class="prose"><h1>404: Game over</h1><p><a href="{urlpath("/")}">Back to deals</a></p></div>'))
    print(f"built {len(posts)} posts ({sum(p['expired'] for p in posts)} expired) -> {OUT}; SITE_URL={SITE_URL}")
    if skipped: print("scheduled (future date, not published):",", ".join(skipped))
if __name__=="__main__": main()
