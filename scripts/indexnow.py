"""배포 직후 바뀐 페이지 주소를 IndexNow로 네이버·빙에 알립니다 (GitHub Actions에서 실행).

사용: python scripts/indexnow.py            # 직전 커밋 대비 바뀐 페이지만
      python scripts/indexnow.py --all      # 사이트맵의 모든 주소
      python scripts/indexnow.py URL ...    # 지정한 주소만
열쇠 파일: src/standalone/<KEY>.txt → https://guwolkh.com/<KEY>.txt
"""
import json, re, subprocess, sys, urllib.request
from pathlib import Path

KEY = "92554f3af565d508e02719712353dfb6"
ROOT = Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))["siteUrl"].rstrip("/")
HOST = SITE.split("//", 1)[1]
ENDPOINTS = ["https://searchadvisor.naver.com/indexnow", "https://api.indexnow.org/indexnow"]


def all_urls():
    cfg = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
    return [SITE + "/"] + [f"{SITE}/{p['slug']}/" for p in cfg.get("pages", [])]


def changed_urls():
    try:
        files = subprocess.check_output(["git", "diff", "--name-only", "HEAD~1", "HEAD"], cwd=ROOT, text=True).split()
    except subprocess.CalledProcessError:
        return all_urls()
    if any(f in ("site.config.json", "build.py") or f.startswith(("src/layout", "src/home")) for f in files):
        return all_urls()
    urls = []
    for f in files:
        m = re.match(r"src/pages/(.+)\.html$", f)
        if m:
            urls.append(f"{SITE}/{m.group(1)}/")
    return urls


def main():
    args = sys.argv[1:]
    urls = all_urls() if args == ["--all"] else (args or changed_urls())
    if not urls:
        print("IndexNow: 바뀐 페이지 없음"); return
    body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"{SITE}/{KEY}.txt", "urlList": urls}).encode()
    for ep in ENDPOINTS:
        req = urllib.request.Request(ep, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print(f"IndexNow {ep}: {r.status} ({len(urls)}개)")
        except urllib.error.HTTPError as e:
            print(f"IndexNow {ep}: {e.code} {e.read()[:200]!r}")
        except Exception as e:
            print(f"IndexNow {ep}: 실패 {e}")
    print("\n".join(urls))


if __name__ == "__main__":
    main()
