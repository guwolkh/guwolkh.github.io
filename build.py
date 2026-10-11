"""site.config.json + src/ 를 합쳐 dist/ 에 완성된 홈페이지를 만듭니다.

실행: python build.py
(Python 3 기본 기능만 사용하므로 따로 설치할 것이 없습니다.)
"""
import json
import re
import shutil
import sys
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DIST = ROOT / "dist"

# 기획서 5번 표현 기준. 빌드할 때마다 검사해서 걸리면 경고를 띄웁니다.
BANNED = [
    (r"완치", "완치"),
    (r"\d+\s*%(?!\s*예약제)", "효과 수치(○○%)"),
    (r"전문(?!가과정)", "'전문' 수식 (수료 과정 정식 명칭 제외)"),
    (r"최고|최초|유일|대표하는|으뜸|No\.?\s*1|넘버원", "최상급 표현"),
    (r"호전|좋아졌|나아졌|사라졌", "치료 결과 문구"),
    (r"전\s*/\s*후|전후\s*비교|비포|애프터", "치료 전후 비교"),
]

def e(s):
    return escape(str(s), quote=True)


def ext_link(url, cls, inner):
    return f'<a class="{cls}" href="{e(url)}" target="_blank" rel="noopener">{inner}</a>'


def render_fields(cfg):
    cards = []
    for f in cfg.get("fields", []):
        link = ext_link(f["link"], "field-link", "관련 글 보기 ›") if f.get("link") else ""
        desc = f'<p class="field-desc">{e(f["desc"])}</p>' if f.get("desc") else ""
        cards.append(f'<div class="field-card"><h3>{e(f["name"])}</h3>{desc}{link}</div>')
    return "\n      ".join(cards)


def render_fields_extra(cfg):
    x = cfg.get("fieldsExtra") or {}
    if not x.get("items"):
        return ""
    return f'<p class="fields-extra"><span>{e(x.get("label", ""))}</span> {e(" · ".join(x["items"]))}</p>'


def render_cases(cfg):
    blog = cfg.get("blogUrl", "")
    cards = []
    for c in cfg.get("cases", []):
        if not c.get("url"):
            continue
        img = (f'<img src="{e(quote(c["image"]))}" alt="" loading="lazy">' if c.get("image")
               else '<span class="case-thumb-empty" aria-hidden="true"></span>')
        tags = "".join(f"<span>{e(k)}</span>" for k in c.get("keywords", []))
        when = f'<time>{e(c["date"])}</time>' if c.get("date") else ""
        cards.append(ext_link(c["url"], "case",
                              f'<div class="case-thumb">{img}</div><div class="case-body">'
                              f'<div class="case-tags">{tags}</div><h3>{e(c.get("title", ""))}</h3>{when}</div>'))
    html = f'<div class="cases">{"".join(cards)}</div>' if cards else ""
    if blog:
        html += f'<div class="case-more">{ext_link(blog, "btn btn-outline", "블로그에서 칼럼 전체 보기")}</div>'
    return html


def render_hours(cfg):
    rows = []
    for h in cfg["hours"]:
        note = f'<small>{e(h["note"])}</small>' if h.get("note") else ""
        rows.append(f'<div class="hours-row"><dt>{e(h["label"])}</dt><dd>{e(h["time"])}{note}</dd></div>')
    return "\n      ".join(rows)


def render_contact(url, label):
    # 링크가 아직 없으면 공개 사이트에 '준비 중'을 띄우지 않고 감춥니다
    return ext_link(url, "contact", f"<span>{label}</span><strong>열기 ›</strong>") if url else ""


def render_social(cfg):
    links = [(cfg.get(k), label) for k, label in
             (("blogUrl", "블로그"), ("youtubeUrl", "유튜브"), ("instagramUrl", "인스타그램"))]
    items = "".join(ext_link(u, "", label) for u, label in links if u)
    return f'<p class="social">{items}</p>' if items else ""


def render_booking_options(cfg):
    out = []
    for key in ("herbalFirstVisit", "general"):
        b = cfg["booking"][key]
        body = f'<strong>{e(b["title"])}</strong><span>{e(b["desc"])}</span>'
        if b.get("url"):
            out.append(ext_link(b["url"], "sheet-option", body))
        else:
            out.append(f'<div class="sheet-option is-pending">{body}<span>온라인 예약 링크 준비 중</span></div>')
    return "\n    ".join(out)


def render_jsonld(cfg):
    a = cfg["address"]
    data = {
        "@context": "https://schema.org",
        "@type": "MedicalClinic",
        "name": cfg["name"],
        "telephone": cfg["phone"],
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "KR",
            "addressRegion": a["region"],
            "addressLocality": a["locality"],
            "streetAddress": a["street"],
        },
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": o["days"],
             "opens": o["opens"], "closes": o["closes"]}
            for o in cfg["openingHoursSchema"]
        ],
        "medicalSpecialty": ", ".join(f["name"] for f in cfg.get("fields", [])),
    }
    if cfg.get("siteUrl"):
        data["url"] = cfg["siteUrl"]
        data["image"] = cfg["siteUrl"].rstrip("/") + "/" + quote(cfg["director"]["photo"])
    # </script> 가 끼어들지 않도록 '<' 를 이스케이프
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")


def build_context(cfg):
    d = cfg["director"]
    q = quote(cfg.get("mapQuery") or cfg["name"])
    site = cfg.get("siteUrl", "").rstrip("/")
    photo = quote(d["photo"])
    kakao, talk = cfg.get("kakaoUrl", ""), cfg.get("talktalkUrl", "")

    start = int(cfg["careerStartYear"])
    return {
        "careerStartYear": str(start),
        "careerYears": str(date.today().year - start + 1),
        "name": e(cfg["name"]),
        "phone": e(cfg["phone"]),
        # 하이픈을 남겨야 휴대폰 전화 앱이 지역번호(032)를 제대로 끊어 보여 줍니다
        "phoneTel": re.sub(r"[^0-9+-]", "", cfg["phone"]),
        "address": e(cfg["address"]["full"]),
        "canonical": f'<link rel="canonical" href="{e(site)}/">' if site else "",
        "ogImage": e(f"{site}/{photo}" if site else photo),
        "jsonld": render_jsonld(cfg),
        "verification": "\n  ".join(
            f'<meta name="{n}" content="{e(cfg[k])}">'
            for n, k in (("naver-site-verification", "naverSiteVerification"),
                         ("google-site-verification", "googleSiteVerification"))
            if cfg.get(k)),
        "directorPhoto": photo,
        "directorPhotoAlt": e(d["photoAlt"]),
        "directorName": e(d["name"]),
        "directorTitle": e(d["title"]),
        "fields": render_fields(cfg),
        "fieldsExtra": render_fields_extra(cfg),
        "cases": render_cases(cfg),
        "hours": render_hours(cfg),
        "hoursNotes": "\n      ".join(f"<li>{e(n)}</li>" for n in cfg.get("hoursNotes", [])),
        "naverMapUrl": f"https://map.naver.com/p/search/{q}",
        "kakaoMapUrl": f"https://map.kakao.com/?q={q}",
        "kakaoContact": render_contact(kakao, "카카오톡"),
        "talktalkContact": render_contact(talk, "네이버 톡톡"),
        # 하단 바 가운데 칸: 카톡 링크가 생기면 카톡, 그전에는 오시는 길
        "thirdBar": (ext_link(kakao, "bb-btn", "카톡") if kakao
                     else '<a class="bb-btn" href="#visit">오시는 길</a>'),
        "bookingOptions": render_booking_options(cfg),
        "socialLinks": render_social(cfg),
        "representative": e(cfg.get("representative", "")),
        "businessNumber": e(cfg.get("businessNumber", "")),
    }


def check_wording(html):
    text = re.sub(r"<script.*?</script>|<[^>]+>", " ", html, flags=re.S)
    problems = []
    for pattern, label in BANNED:
        for m in re.finditer(pattern, text):
            around = text[max(0, m.start() - 15): m.end() + 15].replace("\n", " ")
            problems.append(f"  - [{label}] …{' '.join(around.split())}…")
    return problems


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cfg = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
    ctx = build_context(cfg)

    template = (SRC / "index.html").read_text(encoding="utf-8")
    missing = set()

    def sub(m):
        key = m.group(1)
        if key not in ctx:
            missing.add(key)
            return m.group(0)
        return ctx[key]

    html = re.sub(r"\{\{(\w+)\}\}", sub, template)
    if missing:
        sys.exit(f"템플릿에 알 수 없는 항목이 있습니다: {', '.join(sorted(missing))}")

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST / "index.html").write_text(html, encoding="utf-8")
    for name in ("style.css", "main.js"):
        shutil.copy2(SRC / name, DIST / name)
    shutil.copytree(ROOT / "images", DIST / "images")

    site = cfg.get("siteUrl", "").rstrip("/")
    robots = "User-agent: *\nAllow: /\n"
    if site:
        robots += f"Sitemap: {site}/sitemap.xml\n"
        (DIST / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"  <url><loc>{e(site)}/</loc></url>\n</urlset>\n", encoding="utf-8")
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")

    print("dist/ 생성 완료")
    pending = [k for k, v in [("한약 초진 예약 링크", cfg["booking"]["herbalFirstVisit"]["url"]),
                              ("일반 진료 예약 링크", cfg["booking"]["general"]["url"]),
                              ("카카오톡 링크", cfg.get("kakaoUrl")),
                              ("네이버 톡톡 링크", cfg.get("talktalkUrl")),
                              ("사이트 주소(siteUrl)", cfg.get("siteUrl"))] if not v]
    if pending:
        print("아직 비어 있는 값: " + ", ".join(pending))

    problems = check_wording(html)
    if problems:
        print("\n[주의] 표현 기준(기획서 5번)에 걸릴 수 있는 문구:")
        print("\n".join(problems))
    else:
        print("표현 기준 검사: 문제 없음")


if __name__ == "__main__":
    main()
