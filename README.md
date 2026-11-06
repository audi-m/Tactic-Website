# TACTIC website (static)

A static rebuild of tacticmi.com, ready to host for free on Azure Static Web Apps.

```
build.py                    builds the site into ./site
content/features.json       the 4 feature detail pages
content/integrations.json   the 9 integrations and 3 categories
content/image-sizes.json    real pixel size of every image (stops pages jumping)
src/assets/                 CSS, JavaScript, and the two web fonts
src/images/                 local images (created by the download script)
staticwebapp.config.json    Azure redirects, 404 page, headers
tools/                      image download scripts
site/                       THE WEBSITE: this folder is what you deploy
```

All URLs match the live Webflow site (`/about`, `/pricing-plan`, `/features/...`,
`/integration/...`), so existing links and Google results keep working.

### Relative links

Every link and file reference is relative, with no leading slash: `assets/css/style.css`
on the home page and `../assets/css/style.css` one folder down. `build.py` works
out the right number of `../` for each page. This means:

- You can double-click any `index.html` in `site/` and the page shows styled,
  and its links take you to the other pages.
- On Azure, a link such as `about/index.html` is redirected to the clean address
  `/about` (the `"trailingSlash": "never"` setting in `staticwebapp.config.json`).
- The 404 page is the one exception: Azure shows it for any missing address at
  any folder depth, so it has `<base href="/">` to keep its links pointing at
  the site root.

Keep writing links as `/about` or `/assets/...` inside `build.py`. The script
converts them when it writes each page.

## Design

Modern startup style: a white page with a soft blue glow behind the hero and
light blue-tinted alternate sections, deep navy text and buttons, Young Serif
headlines with Inter body text, product screenshots shown inside app-window
frames, a tabbed feature explorer, and a "How Tactic works" list that
highlights each step as you scroll.

All colors are variables at the top of `src/assets/css/style.css`: `--bg`
(page), `--bg-2` (tinted sections), `--glow` (hero wash), and `--ink` (navy).
Change them there to restyle every page at once.

**Logo:** the Webflow logo file has wide empty margins and a small tagline under
the letters, which made the wordmark tiny. The site crops it to just the TACTIC
letters and shows them solid dark. To change the size, edit `--logo-h` (the
height of the letters) in the `.logo` rule: 30px in the header, 26px on phones,
28px in the footer.

### Motion and scrolling

- **Hero:** the headline, buttons, and product window settle in once on page load.
  The two small cards drift slightly as you scroll (desktop only).
- **Feature tabs:** panels cross-fade. The section keeps one height, so the page
  never jumps when you switch. Arrow, Home, and End keys work.
- **How Tactic works:** the step nearest the middle of the screen lights up, a
  line fills down the list, and the pinned window cross-fades to that step's
  screenshot. On phones, each step shows its own screenshot instead.
- **Logo strip:** loops seamlessly, pauses on hover, and stops when off screen.
- **Small touches:** FAQ answers slide open, the Monthly/Yearly switch slides,
  the header gains a shadow once you scroll, and the phone menu covers the
  screen and locks the page behind it.
- **Reduced motion:** visitors who turn on "reduce motion" in their device
  settings get the same states with no movement.
- All scroll effects share one `requestAnimationFrame` loop in
  `src/assets/js/main.js`, so fast scrolling stays smooth.

**No layout jumps.** Every image gets its real width and height from
`content/image-sizes.json`, so space is reserved before the image arrives. If
you add an image, add its size there (any image editor shows it).

**Fonts** (Young Serif and Inter, SIL Open Font License) are hosted with the
site and preloaded, so headings don't re-wrap when the font arrives, and the
site doesn't depend on Google Fonts.

## 1. Before you cancel Webflow: download the images

Right now the pages load images from Webflow's CDN. Pull them into the project
while your Webflow plan is still active:

```
python tools/download_images.py          (Mac, Linux, or Windows with Python)
powershell -ExecutionPolicy Bypass -File tools\download-images.ps1   (Windows)
python build.py
```

`build.py` then switches every image to the local copy. It prints how many
images are local; you want "0 still on Webflow's CDN".

## 2. Deploy to Azure Static Web Apps (free)

1. Create a GitHub repository and push this whole folder to it.
2. In the Azure portal: Create a resource > Static Web App.
   - Plan type: **Free**
   - Source: GitHub, pick your repo and the `main` branch
   - Build presets: **Custom**
   - App location: `site`
   - Api location: (leave empty)
   - Output location: (leave empty)
3. Azure adds a GitHub Actions workflow to the repo and deploys. Every time you
   push, the site redeploys.

Because `site/` is committed already built, Azure doesn't need Python. After any
edit, run `python build.py` and push.

## 3. Point your domain

In the Static Web App: Custom domains > Add. Follow the prompts to add the
TXT/CNAME (or ALIAS for the root domain) records at your DNS provider, then
remove the old Webflow DNS records. SSL is issued automatically.

Only cancel Webflow hosting once tacticmi.com loads from Azure.

## 4. Contact form

Static hosting can't send email by itself. Two options:

- **Default (works now):** the form opens the visitor's email app with the
  message filled in, addressed to info@tacticmi.com.
- **Recommended:** create a free form at formspree.io (or similar), copy its
  endpoint URL into `FORM_ENDPOINT` at the top of `build.py`, rebuild, and push.
  Submissions then arrive in your inbox without the visitor leaving the page.

## Editing content

- Feature pages: `content/features.json`
- Integrations: `content/integrations.json` (add an item and its page,
  card, and category listing are generated)
- Home, About, Pricing, Contact text: the `build_*` functions in `build.py`
- Prices: the `PLANS` block in `build.py`

Run `python build.py` after any change.

## Changes from the Webflow site (review these)

The Webflow site still had leftover text from the template it was built on.
I cleaned it up rather than copying it over:

- Removed template FAQ text about "SaaSilo", Google Workspace, and text-message
  marketing from the Features and Integrations pages; they now show TACTIC FAQs.
- Removed the generic "Integrating CRM Software" and "Integrated Formatting
  Tools" sections from every integration page.
- Feature page heading changed from "Explore all our CRM features" to
  "Everything your PMO needs".
- "EMP & SPM" in the Office 365 steps changed to "Tactic".
- The product name is written "Tactic" in body text everywhere (the old site
  mixed "Tactic" and "TACTIC"). The logo still reads TACTIC.
- The SAP page had no real content (its text described Zoho). It now has a
  short neutral description and a Connect button. **Please write proper SAP copy.**
- "How X enhanced conversions and TACTIC" headings changed to
  "How Tactic works with X".
- Every "Book a Demo" button now goes to your Calendly link (several were
  empty `#` links).
- Removed the Facebook and Twitter footer links (they pointed to facebook.com
  and twitter.com, not your pages). Add your profile URLs in `footer()` if you have them.
- Removed the animated stats strip ("Success stories / No code customization /
  Actual usage"), because the real figures weren't readable from the live site.
- New, shorter copy written for the modern layout, all based on your existing
  claims: the hero ("The AI-powered PMO for government and enterprise"), the
  four "How Tactic works" steps, the three "Why PMOs choose Tactic" reasons,
  the closing call to action, and the footer tagline. Edit them in
  `build_home()`.
- The Jordan address uses the home-page version ("Business Park Building 23,
  King Abdullah II Street"); the Contact page on Webflow had it slightly differently.
- `/user-authentication/sign-up` (a template page) now redirects to the
  TACTIC app sign-up.

The integration URLs still use the template's slugs (`/integration/softxon` is
MS Project Server, and so on) so existing links don't break. If you want clean
URLs like `/integration/ms-project-server`, change the `slug` in
`integrations.json` and add a 301 redirect for the old one in
`staticwebapp.config.json`.
