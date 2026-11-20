"""Publish due Instagram posts / stories / reels from schedule.json.

Runs from GitHub Actions every 15 min. Media are served from this public repo
(raw.githubusercontent.com). Tokens come from env vars, never from files.
"""
import json, os, sys, time, datetime, urllib.parse, urllib.request

API = "https://graph.instagram.com/v23.0"
TZ = datetime.timezone(datetime.timedelta(hours=8))          # Asia/Taipei
REPO = os.environ.get("GITHUB_REPOSITORY", "")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/"
ACCOUNTS = {  # account key -> env var holding that account's token
    "electricity": "IG_TOKEN_ELECTRICITY",
    "electronics": "IG_TOKEN_ELECTRONICS",
}
DRY = os.environ.get("DRY_RUN") == "1"


def call(method, path, token, **params):
    params["access_token"] = token
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path}: {e.code} {e.read().decode()[:400]}")


def wait_ready(cid, token, limit=300):
    t0 = time.time()
    while time.time() - t0 < limit:
        st = call("GET", cid, token, fields="status_code").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {cid} {st}")
        time.sleep(5)
    raise RuntimeError(f"container {cid} not ready")


def container(token, kind, url, caption=None, child=False):
    p = {}
    if kind == "image":
        p["image_url"] = url
    elif kind == "story_image":
        p.update(image_url=url, media_type="STORIES")
    elif kind == "story_video":
        p.update(video_url=url, media_type="STORIES")
    elif kind == "reel":
        p.update(video_url=url, media_type="REELS", share_to_feed="true")
    if child:
        p["is_carousel_item"] = "true"
    if caption:
        p["caption"] = caption
    cid = call("POST", "me/media", token, **p)["id"]
    if kind in ("reel", "story_video"):
        wait_ready(cid, token)
    return cid


def publish(item, token):
    urls = [RAW + urllib.parse.quote(m) for m in item["media"]]
    t, cap = item["type"], item.get("caption")
    if t == "carousel":
        kids = [container(token, "image", u, child=True) for u in urls]
        for k in kids:
            wait_ready(k, token)
        cid = call("POST", "me/media", token, media_type="CAROUSEL",
                   children=",".join(kids), caption=cap or "")["id"]
        wait_ready(cid, token)
    elif t == "image":
        cid = container(token, "image", urls[0], cap)
        wait_ready(cid, token)
    elif t == "story":
        kind = "story_video" if urls[0].endswith(".mp4") else "story_image"
        cid = container(token, kind, urls[0])
        wait_ready(cid, token)
    elif t == "reel":
        cid = container(token, "reel", urls[0], cap)
    else:
        raise ValueError(t)
    return call("POST", "me/media_publish", token, creation_id=cid)["id"]


def main():
    sched = json.load(open("schedule.json", encoding="utf-8"))
    done = json.load(open("published.json", encoding="utf-8")) if os.path.exists("published.json") else {}
    now = datetime.datetime.now(TZ)
    errors = 0
    for item in sched:
        key = item["id"]
        if key in done:
            continue
        when = datetime.datetime.fromisoformat(item["when"]).replace(tzinfo=TZ)
        if when > now:
            continue
        if now - when > datetime.timedelta(hours=6):        # too late: skip, don't post stale content
            done[key] = {"skipped": "late", "at": now.isoformat()}
            print("SKIP late", key)
            continue
        token = os.environ.get(ACCOUNTS[item["account"]], "")
        if DRY or not token:
            print("DRY" if DRY else "NO TOKEN", key, item["type"], item["media"])
            continue
        try:
            mid = publish(item, token)
            done[key] = {"media_id": mid, "at": datetime.datetime.now(TZ).isoformat()}
            print("OK", key, mid)
        except Exception as e:
            errors += 1
            print("FAIL", key, e)
    json.dump(done, open("published.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
