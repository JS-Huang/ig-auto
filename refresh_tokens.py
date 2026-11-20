"""Refresh long-lived Instagram tokens (valid 60 days) and print new ones as GitHub secret updates."""
import json, os, subprocess, urllib.request
for acc, env in {"electricity": "IG_TOKEN_ELECTRICITY", "electronics": "IG_TOKEN_ELECTRONICS"}.items():
    tok = os.environ.get(env)
    if not tok:
        continue
    url = "https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=" + tok
    new = json.load(urllib.request.urlopen(url, timeout=60))["access_token"]
    subprocess.run(["gh", "secret", "set", env, "--body", new], check=True)
    print("refreshed", acc)
