#!/usr/bin/env python3
"""
Builds the TACTIC website into ./site as plain static HTML.

    python build.py

No packages needed (Python 3.8+). Edit text in content/*.json or in the page
functions below, run the script again, and deploy the ./site folder.

Images: pages use Webflow's CDN until you run tools/download_images.py (or
tools/download-images.ps1). After that, every image found in src/images is
used locally and the site no longer depends on Webflow.
"""
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "site"
DOMAIN = "https://tacticmi.com"

CDN = {
    "CDN1": "https://cdn.prod.website-files.com/688fc0ed4b947555d40bcf06/",
    "CDN2": "https://cdn.prod.website-files.com/688fc0ee4b947555d40bcfc9/",
}

APP_SIGNUP = "https://app.tacticu.com/register-tenant"
APP_LOGIN = "https://app.tacticu.com/"
DEMO = "https://calendly.com/tacticmi/45min"
EMAIL = "info@tacticmi.com"
PHONE = "(+1) 209-345-2856"
PHONE_TEL = "+12093452856"

# Contact form: paste a Formspree (or similar) endpoint here to receive
# submissions by email. Left empty, the form opens the visitor's email app.
FORM_ENDPOINT = ""

FEATURES = json.loads((ROOT / "content/features.json").read_text(encoding="utf-8"))
INTEGRATIONS = json.loads((ROOT / "content/integrations.json").read_text(encoding="utf-8"))
CATS = {c["slug"]: c["name"] for c in INTEGRATIONS["categories"]}
INT_BY_SLUG = {i["slug"]: i for i in INTEGRATIONS["items"]}
TILES = ["sky", "peach", "lilac", "mint", "lemon"]

IMAGE_SIZES = json.loads((ROOT / "content/image-sizes.json").read_text(encoding="utf-8"))

image_manifest = {}  # remote url -> local file name
src_sizes = {}       # src as written in the HTML -> (width, height)
pages_built = []


def e(text):
    return html.escape(str(text), quote=True)


def local_name(url):
    name = unquote(url.rsplit("/", 1)[-1])
    return "".join(c if c.isalnum() or c in "._-" else "-" for c in name)


def img(ref):
    """Return the URL for an image: local copy if downloaded, else Webflow CDN."""
    if ":" in ref and ref.split(":", 1)[0] in CDN:
        key, file = ref.split(":", 1)
        url = CDN[key] + file
    else:
        url = ref
    name = local_name(url)
    image_manifest[url] = name
    src = "/images/" + name if (SRC / "images" / name).exists() else url
    size = IMAGE_SIZES.get(name) or (IMAGE_SIZES["_integration_icon_default"] if "integration-icon" in name else None)
    if size:
        src_sizes[src] = size
    return src


IMG_TAG = re.compile(r"<img\b[^>]*>")


def add_image_sizes(page):
    """Give every <img> its real width/height so nothing jumps while images load."""
    def fix(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        if not src:
            return tag
        if "decoding=" not in tag:
            tag = tag[:-1] + ' decoding="async">'
        size = src_sizes.get(html.unescape(src.group(1)))
        if size and " width=" not in tag:
            tag = tag[:-1] + f' width="{size[0]}" height="{size[1]}">'
        return tag
    return IMG_TAG.sub(fix, page)


LOGO = "CDN1:688fc35926d2687b7bcc5e8e_tactic-white.svg"


def logo():
    """The TACTIC wordmark.

    The Webflow logo file has wide empty margins and a tiny tagline, which made
    the letters only ~11px tall in the header. style.css crops the image to just
    the letters, so the wordmark fills its space, and turns it dark for the
    light background.
    """
    return (f'<a class="logo" href="/" aria-label="TACTIC home">'
            f'<span class="logo-crop"><img src="{img(LOGO)}" alt=""></span></a>')
FAVICON = "CDN1:68b59d3f53a57fca51026693_logo.png"

ICONS = {  # small inline line icons for pills
    "grid": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="2" y="2" width="5" height="5" rx="1"/><rect x="9" y="2" width="5" height="5" rx="1"/><rect x="2" y="9" width="5" height="5" rx="1"/><rect x="9" y="9" width="5" height="5" rx="1"/></svg>',
    "gantt": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M2 4h6M5 8h7M3 12h5"/></svg>',
    "target": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><circle cx="8" cy="8" r="6"/><circle cx="8" cy="8" r="3"/><circle cx="8" cy="8" r=".6" fill="currentColor"/></svg>',
    "gate": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"><path d="M2 8h3l2-4 2 8 2-4h3"/></svg>',
    "shield": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"><path d="M8 2l5 2v4c0 3-2.2 5-5 6-2.8-1-5-3-5-6V4z"/><path d="M8 6v3M8 11v.01" stroke-linecap="round"/></svg>',
}


# ---------------------------------------------------------------- layout ----

def head(title, description, path, og_image=None):
    og = img(og_image or "CDN1:68990b185ceaea2df10a3e21_dashboard-dark.png")
    og_abs = og if og.startswith("http") else DOMAIN + og
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.classList.add("js")</script>
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{DOMAIN}{path}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="{e(og_abs)}">
<meta property="og:url" content="{DOMAIN}{path}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(description)}">
<meta name="theme-color" content="#FFFFFF">
<link rel="icon" href="{img(FAVICON)}">
<link rel="preload" href="/assets/fonts/young-serif-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/inter-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
"""


def header(current):
    def nav(href, label, key):
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{href}"{cur}>{label}</a>'

    return f"""<header class="site-header">
  <div class="wrap">
    {logo()}
    <div class="nav-panel" id="site-menu">
    <nav class="nav" aria-label="Main">
      <div class="nav-group">
        <button class="nav-trigger" aria-expanded="false" aria-haspopup="true">Product</button>
        <div class="nav-menu">
          <a href="/">PMO platform<small>Strategy and project execution</small></a>
          <a href="/feature">Features<small>Everything Tactic does</small></a>
          <a href="/integration">Integrations<small>Connect the systems you run</small></a>
        </div>
      </div>
      {nav('/feature', 'Features', 'feature')}
      {nav('/integration', 'Integrations', 'integration')}
      {nav('/pricing-plan', 'Pricing', 'pricing')}
      {nav('/about', 'About', 'about')}
      {nav('/contact', 'Contact', 'contact')}
    </nav>
    <div class="header-actions">
      <a class="btn btn-ghost" href="{APP_LOGIN}">Log in</a>
      <a class="btn btn-primary" href="{APP_SIGNUP}">Get started free</a>
    </div>
    </div>
    <button class="menu-toggle" aria-expanded="false" aria-controls="site-menu" aria-label="Open menu"><span class="bars"></span></button>
  </div>
</header>
<main id="main">
"""


def window(ref, alt, lazy=True, stage=False, priority=False):
    """A screenshot in an app-window frame.

    stage=True gives the frame a fixed shape, so swapping screenshots of different
    sizes (tabs, "How it works") never changes the height of the page. ref may be a
    list of (ref, alt) pairs; they are stacked and cross-faded by main.js.
    """
    loading = ' loading="lazy"' if lazy else ""
    if priority:
        loading += ' fetchpriority="high"'
    shots = ref if isinstance(ref, list) else [(ref, alt)]
    imgs = "".join(
        f'<img src="{img(r)}" alt="{e(a)}"{loading}{" class=" + chr(34) + "is-on" + chr(34) if k == 0 and len(shots) > 1 else ""}>'
        for k, (r, a) in enumerate(shots))
    body_cls = "window-body stage" if stage else "window-body"
    return f"""<div class="window">
  <div class="window-bar" aria-hidden="true"><span class="dots"><i></i><i></i><i></i></span></div>
  <div class="{body_cls}">{imgs}</div>
</div>"""


def cta_band(title="Run your PMO on Tactic",
             text="Start a 14-day free trial, or book a 45-minute demo with our team in Lansing or Amman."):
    return f"""<section class="cta-wrap">
  <div class="wrap">
    <div class="cta-panel">
      <h2>{e(title)}</h2>
      <p class="lede">{e(text)}</p>
      <div class="btn-row" style="justify-content:center">
        <a class="btn btn-ghost btn-lg" href="{DEMO}" style="background:rgba(255,255,255,.7)">Book a demo</a>
        <a class="btn btn-primary btn-lg" href="{APP_SIGNUP}">Get started free</a>
      </div>
    </div>
  </div>
</section>
"""


def footer():
    return f"""</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-brand">
        {logo()}
        <p>AI-powered project management and strategy execution for PMOs and SMOs.</p>
      </div>
      <div>
        <h2>Product</h2>
        <ul>
          <li><a href="/feature">Features</a></li>
          <li><a href="/integration">Integrations</a></li>
          <li><a href="/pricing-plan">Pricing</a></li>
          <li><a href="{APP_LOGIN}">Log in</a></li>
          <li><a href="{APP_SIGNUP}">Sign up</a></li>
        </ul>
      </div>
      <div>
        <h2>Company</h2>
        <ul>
          <li><a href="/about">About</a></li>
          <li><a href="/contact">Contact</a></li>
          <li><a href="{DEMO}">Book a demo</a></li>
          <li><a href="https://www.linkedin.com/company/tacticmi/">LinkedIn</a></li>
          <li><a href="https://www.youtube.com/@Tacticu">YouTube</a></li>
        </ul>
      </div>
      <div>
        <h2>Offices</h2>
        <address>155 Cascade Blvd, Lansing, MI 48912, United States</address>
        <address>Business Park Building 23, King Abdullah II Street, Amman, Jordan</address>
        <ul>
          <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
          <li><a href="tel:{PHONE_TEL}">{PHONE}</a></li>
        </ul>
      </div>
    </div>
    <p class="footer-tagline">From strategy to delivery.</p>
    <div class="footer-bottom">
      <span>Copyright © <span data-year>2026</span> SpaceOne Technologies Inc.</span>
      <span>Built for PMOs and SMOs in government and enterprise</span>
    </div>
  </div>
</footer>
<script src="/assets/js/main.js" defer></script>
</body>
</html>
"""


def crumbs(items):
    parts = ['<a href="/">Home</a>']
    for href, label in items:
        parts.append('<span aria-hidden="true">/</span>')
        parts.append(f'<a href="{href}">{e(label)}</a>' if href else f'<span aria-current="page">{e(label)}</span>')
    return f'<nav class="crumbs" aria-label="Breadcrumb">{"".join(parts)}</nav>'


def page_hero(title, sub, trail, extra=""):
    sub_html = f'<p class="lede">{e(sub)}</p>' if sub else ""
    return f"""<section class="page-hero">
  <div class="wrap">
    {crumbs(trail)}
    <h1>{e(title)}</h1>
    {sub_html}
    {extra}
  </div>
</section>
"""


def checks(items):
    return '<ul class="checks">' + "".join(f"<li>{e(i)}</li>" for i in items) + "</ul>"


def faq_block(qa, title="Frequently asked questions", intro=None, tint=False):
    items = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in qa)
    intro_html = f'<p class="lede">{e(intro)}</p>' if intro else ""
    return f"""<section class="section{' tint' if tint else ''}">
  <div class="wrap">
    <div class="section-head center"><h2>{e(title)}</h2>{intro_html}</div>
    <div class="faq-list">{items}</div>
  </div>
</section>
"""


LOCAL_REF = re.compile(r'''(?<!<base )(\b(?:href|src)=")/(?!/)([^"]*)"|(url\(['"]?)/(?!/)''')


def relativize(page, depth):
    """Turn every site-internal link into a relative one ("assets/...", "../about/index.html").

    Pages are written while thinking in site-root paths ("/assets/css/style.css",
    "/about"); this rewrites them for the folder the page lives in, so the site
    works from Azure and when you open the files straight from disk.
    """
    up = "../" * depth

    def page_target(t):
        path, hash_, frag = t.partition("#")
        if path in ("", "/"):
            path = "index.html"
        elif not path.startswith(("assets/", "images/")) and "." not in path.rsplit("/", 1)[-1]:
            path = path.rstrip("/") + "/index.html"  # a page: point at its file
        return up + path + hash_ + frag

    def fix(m):
        if m.group(1):
            return f'{m.group(1)}{page_target(m.group(2))}"'
        return m.group(3) + up  # url(/images/x) inside a style attribute
    return LOCAL_REF.sub(fix, page)


def write(path, body):
    if path == "/":
        out, depth = OUT / "index.html", 0
    elif path == "/404":
        out, depth = OUT / "404.html", 0
    else:
        out = OUT / path.strip("/") / "index.html"
        depth = path.strip("/").count("/") + 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(relativize(add_image_sizes(body), depth), encoding="utf-8")
    if path != "/404":
        pages_built.append(path)


# ------------------------------------------------------------- content ----

HOME_FAQ = [
    ("Can Tactic integrate with our existing systems?",
     "Yes. The Tactic Integration Gateway connects your internal and external systems without coding, so data flows smoothly and you avoid costly middleware."),
    ("Where is Tactic hosted, and can we run it on-premise?",
     "Tactic runs in our secure cloud, your private cloud, or fully on-premise, so you can meet internal policies, compliance, and data residency requirements."),
    ("Does Tactic support both Arabic and English?",
     "Yes. Tactic is fully bilingual with native Arabic and English support, so regional teams work in their language without losing localization quality."),
    ("How secure is Tactic?",
     "Tactic follows enterprise-grade security standards, including encryption in transit and at rest, role-based access control, and compliance with regional data protection laws. In our SaaS model, each customer gets a dedicated database for complete data isolation."),
    ("Is Tactic customizable without coding?",
     "Yes. The no-code form builder, workflow manager, and report designer let you adapt workflows, dashboards, and reports to your processes. No developer required."),
    ("Does Tactic offer AI features?",
     "Yes. Tactic includes AI-powered analytics, portfolio planning, cost and resource allocation optimization, task prioritization, performance forecasting, and risk prediction that flags issues before they affect your projects."),
    ("What is the technology stack behind Tactic?",
     "Vue.js and Nuxt on the front end, a .NET Core API with an API gateway on the back end, MS SQL Server for data, and a microservices architecture for flexibility, performance, and easy integration."),
]

FEATURE_FAQ = [
    ("How does Tactic support both Waterfall and Agile?",
     "Waterfall projects get Gantt charts, dependencies, and critical path monitoring. Agile teams get Kanban boards and Scrum sprints. Both roll up into the same portfolio view."),
    ("How does Tactic track performance and tasks?",
     "Real-time reports and KPIs show task status, progress against plan, workflow bottlenecks, and the project's critical path."),
    ("Can I link tasks and set dependencies?",
     "Yes. Set dependencies between tasks, and if one slips, Tactic immediately shows the impact on the project timeline."),
    ("Is Tactic suitable for both small and large organizations?",
     "Yes. Small teams can work on simple visual boards, while large enterprises get detailed Waterfall planning with complex dependencies."),
]

PLANS = {
    "monthly": [
        dict(name="Basic", badge="Popular", sub="For teams up to 50 users", price="$85", unit="/seat/month", featured=True,
             account=["Up to 50 users", "Built-in identity management", "Cloud integrations"],
             platform=["Project management", "Strategy planning and execution", "Resource and cost management", "AI usage at $0.01 per 1,000 tokens"],
             cta=("Get started free", APP_SIGNUP)),
        dict(name="Enterprise", badge="", sub="Advanced features and reporting", price="Custom", unit="", featured=False,
             account=["Unlimited users", "Custom identity management", "Cloud and on-premise integrations"],
             platform=["Project management", "Strategy planning and execution", "Resource and cost management", "Fine-tuned local AI model"],
             cta=("Contact sales", "/contact")),
    ],
    "yearly": [
        dict(name="Starter", badge="Popular", sub="For teams up to 50 users", price="$65", unit="/seat/month", featured=True,
             account=["Up to 50 users", "Built-in identity management", "Cloud integrations"],
             platform=["Project management", "Strategy planning and execution", "Resource and cost management", "AI usage at $0.01 per 1,000 tokens"],
             cta=("Get started free", APP_SIGNUP)),
        dict(name="Business", badge="", sub="Advanced features and reporting", price="Custom", unit="", featured=False,
             account=["Unlimited users", "Custom identity management", "Cloud and on-premise integrations"],
             platform=["Project management", "Strategy planning and execution", "Resource and cost management", "Fine-tuned local AI model"],
             cta=("Contact sales", "/contact")),
    ],
}


def pricing_block():
    def plan_html(p):
        badge = f'<span class="badge">{e(p["badge"])}</span>' if p["badge"] else ""
        unit = f' <small>{e(p["unit"])}</small>' if p["unit"] else ""
        primary = "btn-primary" if p["featured"] else "btn-ghost"
        return f"""<article class="plan{' featured' if p['featured'] else ''}">
  <div class="plan-top"><h3>{e(p['name'])}</h3>{badge}</div>
  <p class="sub">{e(p['sub'])}</p>
  <div class="price">{e(p['price'])}{unit}</div>
  <h4>Account and support</h4>{checks(p['account'])}
  <h4>Platform access</h4>{checks(p['platform'])}
  <a class="btn {primary}" href="{p['cta'][1]}">{e(p['cta'][0])}</a>
</article>"""

    monthly = "".join(plan_html(p) for p in PLANS["monthly"])
    yearly = "".join(plan_html(p) for p in PLANS["yearly"])
    return f"""<div class="center"><div class="billing" role="group" aria-label="Billing period">
  <button type="button" data-plan="monthly" aria-pressed="true">Monthly</button>
  <button type="button" data-plan="yearly" aria-pressed="false">Yearly</button>
</div></div>
<div class="plans" id="plans-monthly">{monthly}</div>
<div class="plans" id="plans-yearly" hidden>{yearly}</div>"""


HOME_INTEGRATION_ICONS = [
    "6897c882c1b0875108584447_688fc0ee4b947555d40bd137_integration-icon-8%20%2812%29.png",
    "689796713567a5277901eeeb_688fc0ee4b947555d40bd137_integration-icon-8%20%2810%29.png",
    "6897967288e73c1fce14df95_688fc0ee4b947555d40bd137_integration-icon-8.png",
    "68979671bc439748363ee46d_688fc0ee4b947555d40bd137_integration-icon-8%20%287%29.png",
    "6897967118d867bb793283a1_688fc0ee4b947555d40bd137_integration-icon-8%20%284%29.png",
    "68979672c228659b20d96d51_688fc0ee4b947555d40bd137_integration-icon-8%20%282%29.png",
    "6897967177f05af9fb057e16_688fc0ee4b947555d40bd137_integration-icon-8%20%289%29.png",
    "68979671cb8bc13c78b79add_688fc0ee4b947555d40bd137_integration-icon-8%20%286%29.png",
    "68979672b132866f78262b7e_688fc0ee4b947555d40bd137_integration-icon-8%20%281%29.png",
    "68979671a0567099881dfedb_688fc0ee4b947555d40bd137_integration-icon-8%20%288%29.png",
    "68979672e06419ffd10070f5_688fc0ee4b947555d40bd137_integration-icon-8%20%283%29.png",
    "6897c8827a57ad607ee4de33_688fc0ee4b947555d40bd137_integration-icon-8%20%2811%29.png",
]

PORTFOLIO = dict(
    slug=None, label="Portfolio & Initiative Management",
    title="Manage portfolios, programs, projects, and initiatives together",
    intro="Align strategy to execution across every organizational level and entity, and track progress, dependencies, and risks in one control panel.",
    icon="CDN1:688fc0ee4b947555d40bd005_customer-stats.png",
    home_image="CDN1:68915628b524ed88c44ab632_it-portfolio.PNG",
)

EXPLORER = [  # (tab label, pill icon, feature, chips)
    ("Portfolios", "grid", PORTFOLIO, [("Portfolios", None), ("Programs", None), ("Initiatives", None)]),
    ("Waterfall & Agile", "gantt", FEATURES[0], [("Gantt", None), ("Kanban", None), ("MS Project", "softxon")]),
    ("Strategy & KPIs", "target", FEATURES[1], [("Objectives", None), ("KPIs", None), ("Power BI", "markeotic")]),
    ("Lifecycle & gates", "gate", FEATURES[2], [("Phase gates", None), ("Approvals", None), ("MS Teams", "sinza")]),
    ("Risk & issues", "shield", FEATURES[3], [("AI prediction", None), ("Risk matrix", None), ("ServiceNow", "xoros")]),
]


def chip_html(label, int_slug):
    icon = f'<img src="{img(INT_BY_SLUG[int_slug]["icon"])}" alt="">' if int_slug else ""
    return f"<li>{icon}{e(label)}</li>"


def explorer():
    tabs, panels = [], []
    for i, (tab, icon, f, chips) in enumerate(EXPLORER):
        tabs.append(f'<button class="pill" role="tab" id="tab-{i}" aria-controls="panel-{i}" aria-selected="{"true" if i == 0 else "false"}">{ICONS[icon]}{e(tab)}</button>')
        intro = f.get("intro")
        link = f'<a class="link" href="/features/{f["slug"]}">Learn about {e(f["label"].lower())}</a>' if f.get("slug") else '<a class="link" href="/feature">See all features</a>'
        panels.append(f"""<div class="panel{' is-active' if i == 0 else ''}" role="tabpanel" id="panel-{i}" aria-labelledby="tab-{i}">
  <div>
    <div class="tile {TILES[i % len(TILES)]}"><img src="{img(f['icon'])}" alt=""></div>
    <h3>{e(f['title'])}</h3>
    <p class="lede">{e(intro)}</p>
    <ul class="chips">{''.join(chip_html(l, s) for l, s in chips)}</ul>
    {link}
  </div>
  {window(f['home_image'], f['label'] + ' in Tactic', stage=True)}
</div>""")
    return f"""<div data-tabs>
  <div class="pills" role="tablist" aria-label="Tactic features">{''.join(tabs)}</div>
  <div class="panels">{''.join(panels)}</div>
</div>"""


# ---------------------------------------------------------------- pages ----

def build_home():
    how_steps = [
        ("Connect your systems",
         "Link MS Project, Office 365, Power BI, SAP, Oracle, and more through the Tactic Integration Hub. No custom development.",
         "CDN1:688fdbfa21c7c8dbde021f0a_project-cards-cropped.PNG", "Projects synced into Tactic"),
        ("Align strategy to delivery",
         "Map objectives and KPIs to portfolios, programs, and projects, so every initiative shows which goal it serves.",
         "CDN2:68949ada04aa5fefbc18d21f_KPI-progress.PNG", "KPI progress in Tactic"),
        ("Govern every phase",
         "Phase gates, approval workflows, and SLA-based escalation keep each project accountable from initiation to closure.",
         "CDN2:68b40b7424bb5571f79f5d2a_Screenshot%202025-08-31%20114420.png", "Approval workflow in Tactic"),
        ("Predict risks and act",
         "AI flags likely issues from real-time project data, and unresolved risks become tracked issues automatically.",
         "CDN2:68b06fd45e51cf001e01bb44_Screenshot%202025-08-28%20180336.png", "Risk register in Tactic"),
    ]
    # Each step carries its own screenshot for phones; on wider screens the
    # pinned window beside the list cross-fades between the same images.
    steps_html = "".join(
        f'<li><span class="tile {TILES[i]}">{i + 1}</span>'
        f'<div><h3>{e(t)}</h3><p>{e(d)}</p>'
        f'<div class="step-shot"><img src="{img(ref)}" alt="{e(alt)}" loading="lazy"></div></div></li>'
        for i, (t, d, ref, alt) in enumerate(how_steps))
    how_shots = [(ref, alt) for _, _, ref, alt in how_steps]

    # Icons are tiny: load them eagerly so none pop in as they scroll past.
    icons = "".join(f'<img src="{img("CDN1:" + f)}" alt="">' for f in HOME_INTEGRATION_ICONS)
    icons_dup = "".join(f'<img src="{img("CDN1:" + f)}" alt="">' for f in HOME_INTEGRATION_ICONS)

    reasons = [
        ("Built for governance", "Phase-gate control, compliance tracking, and approval workflows designed for government and enterprise oversight."),
        ("No-code by design", "Adapt forms, workflows, dashboards, and reports to your exact processes in minutes, without a developer."),
        ("Arabic, English, and your cloud", "Native bilingual interface, hosted in our cloud, your private cloud, or fully on-premise. Supported by a local team in the region."),
    ]
    reasons_html = "".join(
        f'<li><div class="tile {TILES[i + 1]}" style="width:44px;height:44px;border-radius:12px;margin-bottom:20px"></div><h3>{e(t)}</h3><p>{e(d)}</p></li>'
        for i, (t, d) in enumerate(reasons))

    body = head("Tactic | The AI-powered PMO for government and enterprise",
                "AI-powered project management and strategy execution platform for PMOs and SMOs in government and enterprise.", "/")
    body += header("home")
    body += f"""<section class="hero">
  <div class="wrap">
    <h1>AI-Powered Project Management &amp; Strategy Execution for PMOs &amp; SMOs</h1>
    <p class="lede">Built for government and enterprise leaders, Tactic aligns strategy, strengthens project governance, and enables AI-powered decisions.</p>
    <div class="trust">
      <span><i class="dot"></i><b>Arabic &amp; English</b> native</span>
      <span class="sep" aria-hidden="true"></span>
      <span>Cloud or <b>on-premise</b></span>
    </div>
    <div class="btn-row" style="justify-content:center">
      <a class="btn btn-ghost btn-lg" href="{DEMO}">Book a demo</a>
      <a class="btn btn-primary btn-lg" href="{APP_SIGNUP}">Get started free</a>
    </div>
    <p class="hero-note">14-day free trial. No credit card required.</p>
  </div>
  <div class="hero-stage">
    {window('CDN1:68990b185ceaea2df10a3e21_dashboard-dark.png', 'Tactic portfolio dashboard', lazy=False, priority=True)}
    <div class="float f-left" aria-hidden="true"><img src="{img('CDN1:688fc3bdcc259ec629c7c07a_kpi-chart.PNG')}" alt=""></div>
    <div class="float f-right" aria-hidden="true"><img src="{img('CDN1:688fc3be8386df55b738064b_project-by-status-1.PNG')}" alt=""></div>
  </div>
</section>

<section class="logos">
  <div class="wrap">
    <p class="sub-label">Works with the systems you already run</p>
    <div class="marquee"><div class="marquee-track"><div class="marquee-set">{icons}</div><div class="marquee-set" aria-hidden="true">{icons_dup}</div></div></div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head center">
      <h2>One platform for the whole PMO</h2>
      <p class="lede">From portfolio planning to daily tasks, Tactic gives PMOs, SMOs, and VROs complete control.</p>
    </div>
    {explorer()}
  </div>
</section>

<section class="section tint">
  <div class="wrap">
    <div class="section-head center"><h2>How Tactic works</h2></div>
    <div class="how">
      <ol class="steps-lit">{steps_html}</ol>
      <div class="how-visual">{window(how_shots, "", stage=True)}</div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head center">
      <h2>Why PMOs choose Tactic</h2>
      <p class="lede">Purpose-built for PMOs and SMOs in government and enterprise.</p>
    </div>
    <ul class="reasons">{reasons_html}</ul>
  </div>
</section>

<section class="section tint">
  <div class="wrap">
    <div class="section-head center">
      <h2>Simple pricing per seat</h2>
      <p class="lede">Start free for 14 days. Move to Enterprise when you need on-premise or a local AI model.</p>
    </div>
    {pricing_block()}
  </div>
</section>
"""
    body += faq_block(HOME_FAQ)
    body += cta_band() + footer()
    write("/", body)


def build_about():
    values = [
        ("Culture of transparency", "You see what we're building, why, and how it's progressing. No hidden agendas."),
        ("Customer obsession", "We listen closely and adapt quickly so every feature fits your goals."),
        ("Shared success", "Our team acts as stakeholders, invested in every client's outcomes."),
        ("Knowledge sharing", "We share best practices and lessons learned long after go-live."),
    ]
    v = "".join(f'<li><div class="tile {TILES[i]}" style="width:40px;height:40px;border-radius:12px;margin-bottom:18px"></div><h3>{e(t)}</h3><p>{e(d)}</p></li>' for i, (t, d) in enumerate(values))
    body = head("About | Tactic", "Tactic brings AI-powered project and strategy execution to governments and enterprises across the Middle East.", "/about")
    body += header("about")
    body += page_hero("Building the PMO platform the region chooses first",
                      "AI-powered project and strategy execution for governments and enterprises, built for the region's largest transformation programs.",
                      [(None, "About")])
    body += f"""<section class="section tint">
  <div class="wrap">
    <div class="section-head center"><h2>What we believe</h2></div>
    <ul class="values">{v}</ul>
  </div>
</section>
<section class="section">
  <div class="wrap split">
    <div>
      <h2>Strategists, engineers, and designers on your side</h2>
      <p class="lede">Our team helps organizations turn big visions into results. We listen first, collaborate openly, and treat Tactic as a partnership, not just a platform.</p>
      <p class="lede">Offices in Lansing, Michigan and Amman, Jordan.</p>
      <div class="btn-row" style="margin-top:28px">
        <a class="btn btn-ghost" href="{DEMO}">Book a demo</a>
        <a class="btn btn-primary" href="{APP_SIGNUP}">Get started free</a>
      </div>
    </div>
    {window('CDN1:68991102d2e3e342ea273e44_Capture.PNG', 'Tactic platform screenshot')}
  </div>
</section>
"""
    body += cta_band() + footer()
    write("/about", body)


def build_pricing():
    body = head("Pricing | Tactic", "Tactic pricing for PMOs and SMOs: per-seat plans for teams up to 50 users and custom enterprise plans.", "/pricing-plan")
    body += header("pricing")
    body += page_hero("Simple pricing per seat", "Start with a 14-day free trial. No credit card required.", [(None, "Pricing")])
    body += f"""<section class="section" style="padding-top:0">
  <div class="wrap">{pricing_block()}</div>
</section>
"""
    body += faq_block(HOME_FAQ[:5], tint=True)
    body += cta_band() + footer()
    write("/pricing-plan", body)


def build_contact():
    endpoint = f' data-endpoint="{e(FORM_ENDPOINT)}"' if FORM_ENDPOINT else ""
    body = head("Contact | Tactic", "Contact Tactic for demos, pricing, and support. Offices in Lansing, Michigan and Amman, Jordan.", "/contact")
    body += header("contact")
    body += page_hero("Talk to the Tactic team", "Questions about a rollout, pricing, or support? We reply within one business day.", [(None, "Contact")])
    body += f"""<section class="section" style="padding-top:0">
  <div class="wrap contact-grid">
    <dl class="info-list">
      <div><dt>Email</dt><dd><a href="mailto:{EMAIL}">{EMAIL}</a><br><a href="mailto:Odai@tacticmi.com">Odai@tacticmi.com</a></dd></div>
      <div><dt>Phone</dt><dd><a href="tel:{PHONE_TEL}">{PHONE}</a></dd></div>
      <div><dt>United States</dt><dd><address>155 Cascade Blvd, Lansing, MI 48912</address></dd></div>
      <div><dt>Jordan</dt><dd><address>Business Park Building 23, King Abdullah II Street, Amman</address></dd></div>
      <div><dt>Prefer a call?</dt><dd><a href="{DEMO}">Book a 45-minute demo</a></dd></div>
    </dl>
    <form class="form" data-contact data-mailto="{EMAIL}"{endpoint} novalidate>
      <h2 style="font-size:2rem;margin:0">Send a message</h2>
      <div class="row">
        <label>Full name<input name="name" autocomplete="name" required></label>
        <label>Work email<input name="email" type="email" autocomplete="email" required></label>
      </div>
      <div class="row">
        <label>Phone <span class="hint">(optional)</span><input name="phone" type="tel" autocomplete="tel"></label>
        <label>Organization <span class="hint">(optional)</span><input name="company" autocomplete="organization"></label>
      </div>
      <label>How can we help?<textarea name="message" required></textarea></label>
      <input class="hp" name="_gotcha" tabindex="-1" autocomplete="off" aria-hidden="true">
      <div><button class="btn btn-primary btn-lg" type="submit">Send message</button></div>
      <p class="form-status" role="status" hidden></p>
    </form>
  </div>
</section>
"""
    body += footer()
    write("/contact", body)


def build_feature_index():
    rows = []
    for i, f in enumerate([PORTFOLIO] + FEATURES):
        text = f"""<div>
    <div class="tile {TILES[i % len(TILES)]}"><img src="{img(f['icon'])}" alt=""></div>
    <h3>{e(f['title'])}</h3>
    <p class="lede">{e(f['intro'])}</p>
    {checks(f['bullets']) if f.get('bullets') else ''}
    {f'<a class="link" href="/features/{f["slug"]}">Learn about {e(f["label"].lower())}</a>' if f.get('slug') else ''}
  </div>"""
        media = window(f["home_image"], f["label"] + " in Tactic")
        inner = text + media if i % 2 == 0 else media + text
        rows.append(f'<section class="section{" tint" if i % 2 else ""}"><div class="wrap split">{inner}</div></section>')
    body = head("Features | Tactic", "Explore Tactic features: portfolios, Waterfall and Agile delivery, strategy and KPI execution, lifecycle control, and AI risk management.", "/feature")
    body += header("feature")
    body += page_hero("Everything your PMO needs", "Plan, govern, and deliver, from portfolio strategy down to daily tasks.", [(None, "Features")])
    body += "".join(rows)
    body += faq_block(FEATURE_FAQ, tint=len(rows) % 2 == 1)
    body += cta_band() + footer()
    write("/feature", body)


def build_feature_pages():
    for idx, f in enumerate(FEATURES):
        points = "".join(f"<li><strong>{e(a)}</strong><span>{e(b)}</span></li>" for a, b in f["points"])
        path = f"/features/{f['slug']}"
        pill = f'<span class="eyebrow-pill"><img src="{img(f["icon"])}" alt="">{e(f["label"])}</span>'
        body = head(f"{f['label']} | Tactic", f["intro"], path, og_image=f["secondary_image"])
        body += header("feature")
        body += f"""<section class="page-hero">
  <div class="wrap">
    {crumbs([('/feature', 'Features'), (None, f['label'])])}
    {pill}
    <h1>{e(f['title'])}</h1>
    <p class="lede">{e(f['intro'])}</p>
    <div class="btn-row" style="justify-content:center">
      <a class="btn btn-ghost btn-lg" href="{DEMO}">Book a demo</a>
      <a class="btn btn-primary btn-lg" href="{APP_SIGNUP}">Get started free</a>
    </div>
  </div>
</section>
<div class="hero-shot">{window(f['secondary_image'], f['label'] + ' screen in Tactic', lazy=False)}</div>
<section class="section">
  <div class="wrap split">
    <div>
      <h2>{e(f['workflow_heading'])}</h2>
      <p class="lede">{e(f['workflow_text'])}</p>
      <ul class="points" style="margin-top:28px">{points}</ul>
    </div>
    {window(f['workflow_image'], f['label'] + ' workflow in Tactic')}
  </div>
</section>
<section class="section tint">
  <div class="wrap narrow">
    <div class="section-head center"><h2>What this helps you do</h2></div>
    {checks(f['helpful'])}
  </div>
</section>
"""
        body += faq_block(FEATURE_FAQ)
        body += cta_band() + footer()
        write(path, body)


def int_cards(items):
    return '<ul class="int-grid">' + "".join(
        f'<li><a href="/integration/{i["slug"]}"><span class="ico"><img src="{img(i["icon"])}" alt="" loading="lazy"></span>'
        f'<div><strong>{e(i["name"])}</strong><span>{e(i["summary"])}</span><em>{e(CATS[i["category"]])}</em></div></a></li>'
        for i in items) + "</ul>"


def cat_pills(current):
    all_cur = ' aria-current="page"' if current is None else ""
    links = [f'<a class="pill" href="/integration"{all_cur}>All</a>']
    for slug, name in CATS.items():
        cur = ' aria-current="page"' if slug == current else ""
        links.append(f'<a class="pill" href="/integration-category/{slug}"{cur}>{e(name)}</a>')
    return '<nav class="pills" aria-label="Integration categories">' + "".join(links) + "</nav>"


INT_FAQ = [HOME_FAQ[0], HOME_FAQ[1], HOME_FAQ[3], HOME_FAQ[4]]


def build_integrations():
    items = INTEGRATIONS["items"]
    body = head("Integrations | Tactic", "Connect Tactic with MS Project Server, Office 365, MS Teams, Zoom, Power BI, ServiceNow, SAP, Oracle, and Excel.", "/integration")
    body += header("integration")
    body += page_hero("Works with the tools your teams already use", "No-code integrations through the Tactic Integration Hub.", [(None, "Integrations")])
    body += f'<section class="section" style="padding-top:0"><div class="wrap">{cat_pills(None)}{int_cards(items)}</div></section>'
    body += faq_block(INT_FAQ, tint=True)
    body += cta_band("Need a system that isn't listed?", "The Integration Hub connects internal and external systems. Tell us what you run and we'll scope it with you.") + footer()
    write("/integration", body)

    for slug, name in CATS.items():
        sub = [i for i in items if i["category"] == slug]
        path = f"/integration-category/{slug}"
        body = head(f"{name} integrations | Tactic", f"Tactic integrations for {name}.", path)
        body += header("integration")
        body += page_hero(f"{name} integrations", "No-code integrations through the Tactic Integration Hub.",
                          [("/integration", "Integrations"), (None, name)])
        body += f'<section class="section" style="padding-top:0"><div class="wrap">{cat_pills(slug)}{int_cards(sub)}</div></section>'
        body += cta_band() + footer()
        write(path, body)

    for i, it in enumerate(items):
        others = [items[(i + k) % len(items)] for k in (1, 2, 3)]
        path = f"/integration/{it['slug']}"
        if it["steps"]:
            right = f"""<div><h3 style="margin-bottom:20px">{e(it['how_heading'])}</h3>
      <ol class="steps">{''.join(f'<li><span>{e(s)}</span></li>' for s in it['steps'])}</ol></div>"""
        else:
            right = f"""<ul class="points"><li><strong>Scoped with you</strong><span>Every {e(it['name'])} landscape is different. Our team maps the data you need and sets up the connection through the Integration Hub.</span></li></ul>"""
        how_text = f'<p class="lede">{e(it["how_text"])}</p>' if it.get("how_text") else ""
        body = head(f"{it['name']} integration | Tactic", it["summary"], path)
        body += header("integration")
        body += f"""<section class="page-hero">
  <div class="wrap">
    {crumbs([('/integration', 'Integrations'), (None, it['name'])])}
    <div class="tile sky" style="width:88px;height:88px;border-radius:24px;margin:0 auto 24px"><img src="{img(it['icon'])}" alt="{e(it['name'])} logo" style="width:52px;height:52px"></div>
    <h1>Tactic + {e(it['name'])}</h1>
    <p class="lede">{e(it['summary'])}</p>
    <div class="btn-row" style="justify-content:center">
      <a class="btn btn-ghost btn-lg" href="/integration">All integrations</a>
      <a class="btn btn-primary btn-lg" href="/contact">Connect {e(it['name'])}</a>
    </div>
  </div>
</section>
<section class="section tint">
  <div class="wrap split top">
    <div>
      <h2>Tactic and {e(it['name'])}</h2>
      <p class="lede">{e(it['intro'])}</p>
      {how_text}
    </div>
    {right}
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="section-head center"><h2>Other integrations</h2></div>
    {int_cards(others)}
  </div>
</section>
"""
        body += cta_band() + footer()
        write(path, body)


def build_404():
    body = head("Page not found | Tactic", "The page you're looking for doesn't exist.", "/404")
    # Azure shows this page for ANY missing address, at any folder depth, so its
    # relative links are anchored to the site root with <base>.
    body = body.replace('<link rel="canonical"', '<base href="/">\n<meta name="robots" content="noindex">\n<link rel="canonical"')
    body += header(None)
    body += """<section class="section notfound">
  <div class="wrap">
    <h1>This page doesn't exist</h1>
    <p class="lede" style="margin:0 auto 28px">The link may be out of date, or the page has moved.</p>
    <div class="btn-row" style="justify-content:center">
      <a class="btn btn-ghost btn-lg" href="/feature">See features</a>
      <a class="btn btn-primary btn-lg" href="/">Go to home page</a>
    </div>
  </div>
</section>
"""
    body += footer()
    write("/404", body)


def build_meta_files():
    urls = "".join(f"  <url><loc>{DOMAIN}{p if p != '/' else ''}</loc></url>\n" for p in pages_built)
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + urls + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n", encoding="utf-8")
    shutil.copy(ROOT / "staticwebapp.config.json", OUT / "staticwebapp.config.json")
    lines = [f"{url}\t{name}" for url, name in sorted(image_manifest.items(), key=lambda x: x[1])]
    (ROOT / "tools" / "images.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(SRC / "assets", OUT / "assets")
    if (SRC / "images").exists():
        shutil.copytree(SRC / "images", OUT / "images")
    build_home()
    build_about()
    build_pricing()
    build_contact()
    build_feature_index()
    build_feature_pages()
    build_integrations()
    build_404()
    build_meta_files()
    local = sum(1 for n in image_manifest.values() if (SRC / "images" / n).exists())
    print(f"Built {len(pages_built)} pages into {OUT}")
    print(f"Images: {local} local, {len(image_manifest) - local} still on Webflow's CDN")


if __name__ == "__main__":
    main()
