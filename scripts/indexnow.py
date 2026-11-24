"""배포 직후 바뀐 페이지 주소를 IndexNow로 네이버·빙에 알립니다 (GitHub Actions에서 실행).

사용: python scripts/indexnow.py            # 이번 푸시(없으면 직전 커밋)에서 바뀐 페이지만
      python scripts/indexnow.py --all      # 사이트맵의 모든 주소
      python scripts/indexnow.py URL ...    # 지정한 주소만
열쇠 파일: src/standalone/<KEY>.txt → https://guwolkh.com/<KEY>.txt
"""
import json, os, re, subprocess, sys, urllib.request
from pathlib import Path

KEY = "92554f3af565d508e02719712353dfb6"
ROOT = Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))["siteUrl"].rstrip("/")
HOST = SITE.split("//", 1)[1]
# 비교 기준: 이번 푸시 직전 커밋(Actions에서 INDEXNOW_BASE로 넘김), 없으면 직전 커밋
def _base():
    b = os.environ.get("INDEXNOW_BASE", "").strip()
    if b and set(b) != {"0"}:
        try:
            subprocess.check_output(["git", "cat-file", "-e", b + "^{commit}"], cwd=ROOT, stderr=subprocess.DEVNULL)
            return b
        except subprocess.CalledProcessError:
            pass
    return "HEAD~1"


ENDPOINTS = ["https://searchadvisor.naver.com/indexnow", "https://api.indexnow.org/indexnow"]


def all_urls():
    cfg = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
    return [SITE + "/"] + [f"{SITE}/{p['slug']}/" for p in cfg.get("pages", [])]


def _pages_at(rev):
    """그 커밋의 site.config.json을 (전체 설정, slug→페이지) 로 돌려줌."""
    raw = subprocess.check_output(["git", "show", f"{rev}:site.config.json"], cwd=ROOT)
    cfg = json.loads(raw)
    return cfg, {p["slug"]: p for p in cfg.get("pages", [])}


def config_changed_urls():
    """site.config.json에서 실제로 바뀐 페이지만 고름.
    페이지 목록 밖의 공통 설정(전화·진료시간 등)이 바뀌면 모든 페이지."""
    try:
        old_cfg, old = _pages_at(_base())
        new_cfg, new = _pages_at("HEAD")
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return all_urls()
    strip = lambda c: {k: v for k, v in c.items() if k != "pages"}
    if strip(old_cfg) != strip(new_cfg):
        return all_urls()
    urls = []
    added = False
    for slug, page in new.items():
        if old.get(slug) != page:
            urls.append(f"{SITE}/{slug}/")
            if slug not in old:
                added = True
                hub = slug.rsplit("/", 1)[0]
                if "/" in slug and hub in new:
                    urls.append(f"{SITE}/{hub}/")  # 새 칼럼이 걸리는 질환 페이지
    if added or set(old) - set(new):
        urls.append(SITE + "/")  # 홈의 칼럼 목록
    return urls


def changed_urls():
    try:
        files = subprocess.check_output(["git", "diff", "--name-only", _base(), "HEAD"], cwd=ROOT, text=True).split()
    except subprocess.CalledProcessError:
        return all_urls()
    # 모든 페이지 모양이 바뀌는 파일이면 전체를 알림
    if any(f == "build.py" or f.startswith(("src/layout", "src/home", "src/style", "src/main")) for f in files):
        return all_urls()
    urls = config_changed_urls() if "site.config.json" in files else []
    for f in files:
        m = re.match(r"src/pages/(.+)\.html$", f)
        if m:
            urls.append(f"{SITE}/{m.group(1)}/")
    return list(dict.fromkeys(urls))


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
