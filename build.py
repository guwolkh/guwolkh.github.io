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
        if f.get("page"):
            link = f'<a class="field-link" href="/{e(f["page"])}/">자세히 보기 ›</a>'
        elif f.get("link"):
            link = ext_link(f["link"], "field-link", "관련 글 보기 ›")
        else:
            link = ""
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


def clinic_jsonld(cfg):
    a = cfg["address"]
    site = cfg.get("siteUrl", "").rstrip("/")
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
        # medicalSpecialty 는 schema.org 정해진 값만 받으므로, 진료 질환은 knowsAbout 로 적습니다
        "knowsAbout": conditions_known(cfg),
        "founder": physician_ref(cfg),
        "employee": physician_ref(cfg),
        "hasMap": "https://map.naver.com/p/search/" + quote(cfg.get("mapQuery") or cfg["name"]),
        "sameAs": [u for u in (cfg.get("blogUrl"), cfg.get("youtubeUrl"), cfg.get("instagramUrl"),
                               cfg.get("naverPlaceUrl"), kakao_channel(cfg)) if u],
    }
    if site:
        data["@id"] = site + "/#clinic"
        data["url"] = site + "/"
        data["image"] = site + "/" + quote(cfg["director"]["photo"])
    return data


def conditions_known(cfg):
    out = []
    for pg in cfg.get("pages", []):
        if pg.get("kind") == "condition":
            out.append(pg["condition"])
            out.extend(pg.get("alternateNames", []))
    return out


def physician_ref(cfg):
    site = cfg.get("siteUrl", "").rstrip("/")
    ref = {"@type": "Physician", "name": cfg["director"]["name"]}
    if site:
        ref = {"@id": site + "/director/#physician", **ref, "url": site + "/director/"}
    return ref


def kakao_channel(cfg):
    # 상담 채팅 주소(…/chat)가 아니라 채널 프로필 주소를 같은 기관 표시로 씁니다
    u = cfg.get("kakaoUrl", "")
    return u[:-len("/chat")] if u.endswith("/chat") else u


def jsonld_tags(items):
    # </script> 가 끼어들지 않도록 '<' 를 이스케이프
    return "\n  ".join(
        '<script type="application/ld+json">'
        + json.dumps(d, ensure_ascii=False).replace("<", "\\u003c") + "</script>" for d in items)


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
        "ogImage": e(f"{site}/{photo}" if site else photo),
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
                     else '<a class="bb-btn" href="/#visit">오시는 길</a>'),
        "bookingOptions": render_booking_options(cfg),
        "socialLinks": render_social(cfg),
        "representative": e(cfg.get("representative", "")),
        "businessNumber": e(cfg.get("businessNumber", "")),
    }


def nav_links(cfg, current):
    items = [(f'/{pg["slug"]}/', pg["nav"], pg["slug"]) for pg in cfg.get("pages", []) if pg.get("nav")]
    items.append(("/#visit", "오시는 길", None))
    out = []
    for href, label, slug in items:
        cur = ' aria-current="page"' if slug and slug == current else ""
        out.append(f'<a href="{e(href)}"{cur}>{e(label)}</a>')
    return "\n    ".join(out)


def footer_links(cfg):
    return "".join(f'<a href="/{e(pg["slug"])}/">{e(pg["nav"])}</a>'
                      for pg in cfg.get("pages", []) if pg.get("nav"))


def render_faq_list(items):
    rows = "".join(
        f'<details class="faq-item"><summary>{e(q["q"])}</summary><p>{e(q["a"])}</p></details>'
        for q in items)
    return f'<div class="faq">{rows}</div>'


def render_faq(items, heading=True):
    if not items:
        return ""
    # FAQ 전용 페이지는 맨 위 제목이 이미 '자주 묻는 질문'이라 섹션 제목을 다시 달지 않습니다
    title = '<p class="kicker">FAQ</p><h2 class="section-title">자주 묻는 질문</h2>' if heading else ""
    return f'<section class="section section-tint" id="faq">{title}{render_faq_list(items)}</section>'


def render_related(items):
    if not items:
        return ""
    links = "".join(f"<li>{ext_link(r['url'], 'related-link', e(r['title']) + ' <span>›</span>')}</li>"
                    for r in items)
    return ('<section class="section" id="related">'
            '<p class="kicker">Column</p><h2 class="section-title">관련 글 (원장 칼럼)</h2>'
            f'<ul class="related">{links}</ul>'
            '<p class="related-note">네이버 블로그로 연결됩니다.</p></section>')


def render_page_cta(cfg):
    notes = "".join(f"<li>{e(n)}</li>" for n in cfg.get("hoursNotes", []))
    return ('<section class="section section-dark page-cta">'
            '<h2 class="section-title">상담 · 예약 안내</h2>'
            f'<dl class="hours hours-dark">{render_hours(cfg)}</dl>'
            f'<ul class="hours-notes">{notes}</ul>'
            '<div class="btn-row">'
            '<button type="button" class="btn btn-light" data-open-booking>네이버로 예약하기</button>'
            f'<a class="btn btn-ghost" href="tel:{e(re.sub(r"[^0-9+-]", "", cfg["phone"]))}">전화 상담 {e(cfg["phone"])}</a>'
            '</div></section>')


def page_jsonld(cfg, pg, url):
    site = cfg.get("siteUrl", "").rstrip("/")
    clinic_ref = {"@id": site + "/#clinic"} if site else {"name": cfg["name"]}
    items = [clinic_jsonld(cfg)]
    kind = pg.get("kind")
    if kind == "condition":
        items.append({
            "@context": "https://schema.org",
            "@type": "MedicalWebPage",
            "name": pg["h1"],
            "url": url,
            "description": pg["description"],
            "about": {"@type": "MedicalCondition", "name": pg["condition"],
                      **({"alternateName": pg["alternateNames"]} if pg.get("alternateNames") else {})},
            "publisher": clinic_ref,
            "author": physician_ref(cfg),
            "inLanguage": "ko",
        })
    elif kind == "director":
        d = cfg["director"]
        items.append({
            "@context": "https://schema.org",
            "@type": "Physician",
            **({"@id": site + "/director/#physician"} if site else {}),
            "name": d["name"],
            "jobTitle": d["title"],
            "url": url,
            "image": (site + "/" + quote(d["photo"])) if site else d["photo"],
            "worksFor": clinic_ref,
            "alumniOf": {"@type": "CollegeOrUniversity", "name": "경희대학교 한의과대학"},
            "knowsAbout": conditions_known(cfg),
            "description": pg["lead"],
            "sameAs": [u for u in (cfg.get("blogUrl"), cfg.get("youtubeUrl")) if u],
        })
    if pg.get("faq"):
        items.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q["q"],
                            "acceptedAnswer": {"@type": "Answer", "text": q["a"]}} for q in pg["faq"]],
        })
    items.append({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": cfg["name"], "item": site + "/"},
            {"@type": "ListItem", "position": 2, "name": pg["nav"], "item": url},
        ],
    })
    return items


def fill(template, ctx):
    missing = set()

    def sub(m):
        key = m.group(1)
        if key not in ctx:
            missing.add(key)
            return m.group(0)
        return ctx[key]

    out = re.sub(r"\{\{(\w+)\}\}", sub, template)
    if missing:
        sys.exit(f"템플릿에 알 수 없는 항목이 있습니다: {', '.join(sorted(missing))}")
    return out


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
    site = cfg.get("siteUrl", "").rstrip("/")
    layout = (SRC / "layout.html").read_text(encoding="utf-8")

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    for name in ("style.css", "main.js"):
        shutil.copy2(SRC / name, DIST / name)
    shutil.copytree(ROOT / "images", DIST / "images")
    # 따로 만든 단독 페이지(예: 모바일 문진 /munjin/)는 그대로 복사
    if (SRC / "standalone").exists():
        shutil.copytree(SRC / "standalone", DIST, dirs_exist_ok=True)

    outputs = {}  # 경로 -> html

    # 홈
    home = cfg["home"]
    home_ctx = dict(ctx)
    home_ctx.update({
        "pageTitle": e(home["title"]),
        "pageDescription": e(home["description"]),
        "ogTitle": e(home["ogTitle"]),
        "canonical": f'<link rel="canonical" href="{e(site)}/">' if site else "",
        "ogUrl": f'<meta property="og:url" content="{e(site)}/">' if site else "",
        "jsonldTags": jsonld_tags([clinic_jsonld(cfg)]),
        "navLinks": nav_links(cfg, None),
        "footerLinks": footer_links(cfg),
        "faqPreview": render_faq_list(next((p for p in cfg.get("pages", []) if p["slug"] == "faq"), {}).get("faq", [])[:4]),
    })
    home_ctx["content"] = fill((SRC / "home.html").read_text(encoding="utf-8"), home_ctx)
    outputs["index.html"] = fill(layout, home_ctx)

    # 하위 페이지
    for pg in cfg.get("pages", []):
        url = f"{site}/{pg['slug']}/"
        body = fill((SRC / "pages" / f"{pg['slug']}.html").read_text(encoding="utf-8"), ctx)
        hero = ('<section class="page-hero">'
                f'<p class="hero-eyebrow">{e(pg.get("eyebrow", ""))}</p>'
                f'<h1 class="page-title">{e(pg["h1"])}</h1>'
                f'<p class="page-lead">{e(pg["lead"])}</p></section>')
        content = (hero + "\n" + body + "\n" + render_faq(pg.get("faq"), heading=pg.get("kind") != "faq") + "\n"
                   + render_related(pg.get("related")) + "\n" + render_page_cta(cfg))
        pctx = dict(ctx)
        pctx.update({
            "pageTitle": e(pg["title"]),
            "pageDescription": e(pg["description"]),
            "ogTitle": e(pg["title"]),
            "canonical": f'<link rel="canonical" href="{e(url)}">' if site else "",
            "ogUrl": f'<meta property="og:url" content="{e(url)}">' if site else "",
            "jsonldTags": jsonld_tags(page_jsonld(cfg, pg, url)),
            "navLinks": nav_links(cfg, pg["slug"]),
            "footerLinks": footer_links(cfg),
            "content": content,
        })
        outputs[f"{pg['slug']}/index.html"] = fill(layout, pctx)

    for path, html in outputs.items():
        out = DIST / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")

    robots = "User-agent: *\nAllow: /\nDisallow: /munjin/\nDisallow: /imyeong/\n"
    if site:
        robots += f"Sitemap: {site}/sitemap.xml\n"
        today = date.today().isoformat()
        urls = [f"{site}/"] + [f"{site}/{pg['slug']}/" for pg in cfg.get("pages", [])]
        (DIST / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"  <url><loc>{e(u)}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
            + "</urlset>\n", encoding="utf-8")
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")

    print(f"dist/ 생성 완료 (페이지 {len(outputs)}개)")
    pending = [k for k, v in [("한약 초진 예약 링크", cfg["booking"]["herbalFirstVisit"]["url"]),
                              ("일반 진료 예약 링크", cfg["booking"]["general"]["url"]),
                              ("카카오톡 링크", cfg.get("kakaoUrl")),
                              ("네이버 톡톡 링크", cfg.get("talktalkUrl")),
                              ("사이트 주소(siteUrl)", cfg.get("siteUrl"))] if not v]
    if pending:
        print("아직 비어 있는 값: " + ", ".join(pending))

    problems = []
    for path, html in outputs.items():
        found = check_wording(html)
        if found:
            problems.append(f" {path}")
            problems.extend(found)
    if problems:
        print("\n[주의] 표현 기준(기획서 5번)에 걸릴 수 있는 문구:")
        print("\n".join(problems))
    else:
        print("표현 기준 검사: 문제 없음")


if __name__ == "__main__":
    main()
