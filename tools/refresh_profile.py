"""Build local README assets from public GitHub data."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from html import escape, unescape
from io import BytesIO
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
LOGIN = "Harishik"
PROJECTS = [
    ("egoversa", "EgoVersa", "Spatial reasoning", "docs/screenshots/05b-perspective.png"),
    ("defeat-cad", "DeFeat", "Engineering tools", "docs/images/compare-dark.png"),
    ("lacunaframe", "LacunaFrame", "Video recovery", "docs/design/02-reconstruction.png"),
    ("solace", "SOLACE", "Orbital forecasting", "assets/live_sky.gif"),
    ("photons-to-power-laws", "Photons to Power Laws", "Gamma-ray burst analysis", "docs/figures/hero.gif"),
]
PAPERS = [
    ("Feature Space Stability", "https://doi.org/10.3390/math14061082", "MRI model generalization"),
    ("Autonomous Disaster Reconnaissance", "https://doi.org/10.3390/telecom7020031", "Published robotics survey"),
]

def request(url):
    headers = {"User-Agent": "Harishik-profile-refresh"}
    with urlopen(Request(url, headers=headers), timeout=25) as response:
        data = response.read(20_000_001)
    if len(data) > 20_000_000:
        raise ValueError(f"Public asset is too large: {url}")
    return data

def public_api(path):
    return json.loads(request(f"https://api.github.com/{path}"))

def public_pins():
    page = request(f"https://github.com/{LOGIN}").decode()
    if f'name="octolytics-dimension-user_login" content="{LOGIN}"'.lower() not in page.lower():
        raise ValueError("Unexpected public profile response")
    if not re.search(r'<h2\b[^>]*>\s*Pinned\b', page):
        return []
    blocks = re.findall(r'<li\b[^>]*class="[^"]*\bjs-pinned-item-list-item\b[^"]*"[^>]*>(.*?)</li>', page, re.S)
    pins = []
    for block in blocks:
        links = re.findall(r'<a\b[^>]+href="([^"]+)"', block)
        urls = [unescape(link) for link in links if re.fullmatch(r'/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', link)
                or re.fullmatch(r'https://gist\.github\.com/[A-Za-z0-9_-]+/[0-9a-f]+', link)]
        if not urls:
            raise ValueError("Could not read public pin link")
        dest = urls[0]
        url = "https://github.com" + dest if dest.startswith("/") else dest
        description = re.search(r'<p\b[^>]*class="[^"]*\bpinned-item-desc\b[^"]*"[^>]*>(.*?)</p>', block, re.S)
        summary = unescape(re.sub(r'<[^>]*>',"",description[1])).strip() if description else ""
        title = dest.rsplit("/",1)[-1] if dest.startswith("/") else (summary or "Gist")
        pins.append({"title":title,"url":url,"summary":summary})
    if not 1 <= len(pins) <= 6:
        raise ValueError("Unexpected number of public pins")
    return pins

def public_image(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"avatars.githubusercontent.com", "raw.githubusercontent.com"}:
        raise ValueError("Unsupported image host")
    return Image.open(BytesIO(request(url)))

def read_calendar():
    url = f"https://github.com/users/{LOGIN}/contributions"
    page = request(url).decode()
    counts = {
        (int(w), int(d)): 0 if n == "No" else int(n.replace(",", ""))
        for d, w, n in re.findall(r'for="contribution-day-component-(\d+)-(\d+)"[^>]*>(No|[\d,]+) contributions? on', page)
    }
    cells = [
        (int(w), int(d), int(level), when)
        for when,d,w,level in re.findall(r'data-date="([\d-]+)" id="contribution-day-component-(\d+)-(\d+)" data-level="([0-4])"', page)
    ]
    if not 360 <= len(cells) <= 373 or len(cells) != len(counts):
        raise ValueError("Unexpected public calendar structure")
    dates = sorted(date.fromisoformat(item[3]) for item in cells)
    if len(set(dates)) != len(cells) or (dates[-1] - dates[0]).days + 1 != len(cells):
        raise ValueError("Incomplete date range")
    if any((counts[(w,d)] > 0) != (level > 0) for w,d,level,_ in cells):
        raise ValueError("Contribution levels disagree with public counts")
    days = [[w,d,level,counts[(w,d)]] for w,d,level,_ in sorted(cells)]
    return days, [d.isoformat() for d in [dates[0], dates[-1]]]

def read_project(spec, stage):
    slug, title, category, image_path = spec
    try:
        data = public_api(f"repos/{LOGIN}/{slug}")
    except HTTPError as error:
        if error.code == 404:
            return None
        raise
    if data["private"]:
        return None
    url = data["html_url"]
    owner = data["owner"]["login"]
    name = data["name"]
    raw = f"https://raw.githubusercontent.com/{owner}/{name}/{quote(data['default_branch'], safe='')}/{quote(image_path)}"
    try:
        with public_image(raw) as im:
            if getattr(im,"n_frames",1) > 1:
                im.seek(im.n_frames//3)
            im = im.convert("RGB")
            im.thumbnail((1200,760))
            im.save(stage/f"{slug}.jpg",quality=89,optimize=True)
        media = f"{slug}.jpg"
    except HTTPError as error:
        if error.code != 404:
            raise
        media = None
    return {
        "title": title, "name": name, "category": category, "summary": data.get("description") or category,
        "url": url, "media": media, "stars": data["stargazers_count"], "pushed": data["pushed_at"],
    }

def build_snapshot(stage):
    source = public_api(f"users/{LOGIN}")
    if source["login"].lower() != LOGIN.lower():
        raise ValueError("Unexpected GitHub account")
    user = {
        "login":source["login"], "name":source["name"], "bio":source["bio"],
        "avatarUrl":source["avatar_url"], "url":source["html_url"], "pins":public_pins(),
    }
    with public_image(user["avatarUrl"]) as avatar:
        avatar.convert("RGB").save(stage/"avatar.jpg",quality=92,optimize=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        featured = [p for p in pool.map(lambda spec: read_project(spec,stage),PROJECTS) if p]
    repositories=public_api(f"users/{LOGIN}/repos?type=owner&sort=pushed&per_page=100")
    excluded={p["name"].lower() for p in featured} | {LOGIN.lower(), "mars-beacon"}
    recent=[
        {"title":p["name"],"url":p["html_url"],"pushed":p["pushed_at"]}
        for p in repositories
        if not p["private"] and not p["fork"] and not p["archived"] and p["name"].lower() not in excluded
    ][:4]
    calendar, dates = read_calendar()
    return {"profile":user,"projects":featured,"recent":recent,"calendar":calendar,"dates":dates}

def bounded_text(value, max_length=170):
    flat = " ".join(value.split())
    if len(flat) > max_length:
        flat = flat[:max_length-1].rstrip()+"…"
    return escape(flat,quote=False).replace("|","&#124;").replace("[","&#91;").replace("]","&#93;").replace("*","&#42;").replace("_","&#95;").replace("~","&#126;").replace("`","&#96;")

def links(items):
    return "\n".join(f'- [**{bounded_text(title)}**]({url}) — {bounded_text(summary)}' for title,url,summary in items)

def readme(snapshot, animated):
    user=snapshot["profile"]
    active=sum(day[2]>0 for day in snapshot["calendar"])
    total=sum(day[3] for day in snapshot["calendar"])
    ext="gif" if animated else "jpg"
    jump="[Still images](STATIC.md)" if animated else "[Motion edition](README.md)"
    def image(name,alt):
        return f'<img src="assets/{name}.{ext}" width="900" alt="{alt}">'
    featured="\n".join(
        f'- [**{bounded_text(p["title"])}**]({p["url"]}) — {bounded_text(p["summary"])}'
        + (f" · Updated {p['pushed'][:10]}" if p.get("pushed") else "")
        for p in snapshot["projects"]
    )
    pins=links((p["title"],p["url"],p["summary"] or "Public pin") for p in user["pins"])
    index=links(PAPERS)
    recent=links((p["title"],p["url"],f"Updated {p['pushed'][:10]}") for p in snapshot.get("recent",[]))
    first,last=snapshot["dates"]
    bio=bounded_text(user.get("bio") or "")
    about="I build AI systems and engineering tools, and publish research on how models perform under changing conditions."
    banner_alt=f"{escape(user.get('name') or user['login'],quote=True)}, AI Engineer and Researcher. Orbital observatory with an animated starfield."
    return f"""{image('observatory', banner_alt)}

## About

**AI Engineer & Researcher** · [ORCID](https://orcid.org/0009-0007-6781-2803) · [LinkedIn](https://www.linkedin.com/in/harishik-dev-singh-jamwal-b31b60288/) · {jump}

{bio or about}

{image('identity', 'Tilted foil card with the current GitHub avatar. Build the tool. Test the idea. Publish the evidence.')}

[Selected work](#selected-work) · [Project index](#project-index) · [Pinned work](#pinned-work) · [Contribution activity](#contribution-activity)

## Selected work

{image('project-reel', 'Reel of public project visuals from the featured repositories.')}

{featured}

## Project index

{image('mixtape', 'Spinning cassette with an equalizer based on weekly public contribution counts.')}

{index}

### Recently updated repositories

{recent or "No additional public repositories."}

## Pinned work

{image('pinned-work', 'Scanning light travels across the current public GitHub pins.')}

{pins or 'No public pins are set.'}

## Contribution activity

{image('activity-replay','A scanning light tracks weekly activity while a spacecraft collects active days across the public contribution calendar.')}

{first} to {last} · **{active} active days** · **{total} public calendar contributions**.

_Project media comes from the public repository documentation._
"""

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot",type=Path)
    args=parser.parse_args()
    with TemporaryDirectory(prefix="harishik-profile-") as temp:
        stage=Path(temp)
        snapshot=json.loads((args.snapshot/"profile.json").read_text()) if args.snapshot else build_snapshot(stage)
        source=args.snapshot or stage
        (stage/"current.json").write_text(json.dumps(snapshot,ensure_ascii=False))
        out=stage/"assets"
        out.mkdir()
        (out/"avatar.jpg").write_bytes((source/"avatar.jpg").read_bytes())
        subprocess.run([sys.executable, str(ROOT/"tools/render_profile.py"), str(stage/"current.json"), str(source), str(out)],check=True)
        (ROOT/"assets").mkdir(exist_ok=True)
        for item in out.iterdir():
            item.replace(ROOT/"assets"/item.name)
        for name,animated in [("README.md",True),("STATIC.md",False)]:
            (ROOT/name).write_text(readme(snapshot,animated))
        (ROOT/"profile.json").write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+"\n")
        print(f"Refreshed {len(snapshot['projects'])} featured projects and {len(snapshot['profile']['pins'])} public pins.")

if __name__ == "__main__":
    main()
