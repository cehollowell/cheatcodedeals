# CheatCodeDeals blog (static site)

## Build
    SITE_URL=https://your-final-domain python3 build.py      # writes ./site/
    python3 build.py --drafts                                 # also include future-dated posts
    BUILD_NOW=2026-10-23T09:00 python3 build.py               # preview the site at another time (expiry testing)
    cd site && python3 -m http.server 8000                    # preview at http://localhost:8000

- Python 3.9+, standard library only.
- `SITE_URL` must be the real public URL, including a project subpath such as `https://cehollowell.github.io/cheatcodedeals`. It's used for absolute og:image/Twitter card links, the RSS feed and sitemap.xml. Root-absolute asset and page links (`/style.css`, `/img/...`, `/deals/...`) are prefixed with that path so they resolve on GitHub project Pages.
- **Rebuild regularly.** The "Expired" label is applied at build time. A daily scheduled build (CI cron) keeps it current.
- Posts with a future `date` are treated as scheduled. They're left out until a build runs after that time (all times are ET).

## Add a post
1. Put the 1600x900 graphic in `static/img/`.
2. Create `posts/YYYY-MM-DD-slug.md`:

```
---
title: Resident Evil 4 Gold Edition
date: 2026-10-19 20:01            # ET publish time
price: $14.99
was: $49.99                       # blank if not a discount
off: 70%                          # blank if not a discount
platform: PS5
store: PlayStation Store
ends: 2026-10-22                  # date = end of day ET, or 2026-10-22T02:59 for an exact time; blank = no end
status: Best price yet            # optional tag, e.g. Lowest price ever
category: Games                   # Games | Electronics | Collectibles & Pokemon | Drops & Announcements
image: /img/2-re4-gold.png
link: https://store.playstation.com/en-us/product/...   # direct store link
---
Body text. Paragraphs are separated by blank lines; **bold** and [links](https://...) work.
```
3. Run `python3 build.py`.

Store links (and links in the body) are passed through `tools/afflink.py` at build time if that file exists. It changes nothing until affiliate IDs are configured.

## Hosting (static: GitHub Pages, Cloudflare Pages or Netlify)
Publish the `site/` folder. It includes `.nojekyll`, `404.html`, `robots.txt`, `sitemap.xml` and `feed.xml`.
`tools/afflink.py` (config in `tools/config.json`) runs during the build. It rewrites store links only after IDs or templates are filled in.

`seed.py` was the one-time import of the Oct 19 and Oct 20 posts; you don't need to run it again.
