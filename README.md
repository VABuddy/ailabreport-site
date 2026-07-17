# The AI Lab Report — Blog Generator & Website

Static site (root landing page + blog) for **theailabreport.com**, plus a
Gemini-powered generator that turns a finished video — or a script — into a
polished, on-brand blog post. Same spirit as the B-Roll Manager: you run a
command, it does the work, originals are never touched.

**Two things live in this folder:**
1. `site/` — the actual website (this is what gets hosted on GitHub Pages).
2. `blog_generator.py` — the tool that writes posts into `site/blog/`.

---

## What's already built

```
blog-generator/
├── blog_generator.py         ← the tool
├── README.md                 ← this file
├── templates/
│   └── post_template.html    ← the template every post is built from
└── site/                     ← THE WEBSITE (host this folder)
    ├── index.html            ← root landing page (theailabreport.com)
    ├── CNAME                 ← tells GitHub the custom domain
    ├── assets/style.css      ← the brand stylesheet (navy/cyan, matches the channel)
    └── blog/
        ├── index.html        ← the blog listing (auto-rebuilt by the tool)
        ├── posts.json        ← the post manifest (the tool maintains this)
        └── posts/
            └── fable-5-returns.html   ← the sample post
```

The site is fully on-brand and ready. The sample Fable 5 post shows exactly
what the tool produces. **Nothing is live until you do the hosting steps below.**

---

## ONE-TIME SETUP

### Step 1 — Install dependencies
You already have Python (from the B-Roll Manager). Add the Gemini library:
```
pip install google-generativeai
```

### Step 2 — API key
The tool reuses the **same Gemini key as the B-Roll Manager**. If that key is
already set as an environment variable, you're done. If not, set it once
(PowerShell):
```
setx GEMINI_API_KEY "your-key-here"
```
Then open a new terminal so it takes effect. (Billing-enabled project, model
`gemini-2.5-flash` — same as B-Roll Manager.)

### Step 3 — Put the site on GitHub Pages (free hosting)
This is the part that makes it live, and it's the path we chose specifically so
the tool can auto-publish later.

1. Create a free account at **github.com** if you don't have one.
2. Create a new **public** repository — name it anything (e.g. `ailabreport-site`).
3. On your PC, in this `blog-generator` folder, run:
   ```
   git init
   git add -A
   git commit -m "Initial site"
   git branch -M main
   git remote add origin https://github.com/YOURNAME/ailabreport-site.git
   git push -u origin main
   ```
4. In the repo on github.com: **Settings → Pages**. Under "Build and deployment",
   set Source = **Deploy from a branch**, Branch = **main**, folder = **/site**,
   then Save.
   *(If GitHub only offers "/ (root)" and not "/site", the simplest fix is to
   move the CONTENTS of the `site/` folder to the repo root before pushing. Ask
   Axiom and we'll adjust — it's a 2-minute change.)*
5. Wait ~1 minute. GitHub gives you a temporary URL like
   `https://yourname.github.io/...` — confirm the site loads there first.

### Step 4 — Point the domain (Namecheap) — **email stays safe**
Your domain is at Namecheap and currently only runs Google Workspace email via
**MX records**. **We do not touch the MX records — email keeps working.** We only
add records that point the *website* at GitHub.

In Namecheap → **Domain List → Manage → Advanced DNS**:

**Add these four A records** (Host = `@`, these are GitHub Pages' IPs):
```
A    @    185.199.108.153
A    @    185.199.109.153
A    @    185.199.110.153
A    @    185.199.111.153
```

**Add one CNAME record** (so www works):
```
CNAME    www    YOURNAME.github.io.
```

**Leave every existing MX record exactly as-is** (that's your Google Workspace /
Kit email — do not delete or change those).

> ⚠️ The four GitHub IPs above are stable but worth a 10-second confirm against
> GitHub's official page ("Managing a custom domain for your GitHub Pages site")
> in case they ever change.

Back in the GitHub repo: **Settings → Pages → Custom domain**, enter
`theailabreport.com`, Save, and tick **Enforce HTTPS** once it's available.
(The `CNAME` file in `site/` already contains the domain, so this should match.)

DNS can take anywhere from a few minutes to a few hours to propagate. Once it
does, `theailabreport.com` shows the landing page and `theailabreport.com/blog`
shows the blog.

### Step 5 — Google Analytics (when ready)
Every page has a GA4 snippet with a placeholder ID `G-XXXXXXXXXX`. Once your
Google Analytics account exists, find-and-replace `G-XXXXXXXXXX` with your real
Measurement ID across all files in `site/` (it appears in `index.html`,
`blog/index.html`, `templates/post_template.html`, and each post). Until then it
does nothing and is safe to leave.

---

## EVERYDAY USE

### Make a post from a finished video (Gemini transcribes it)
```
python blog_generator.py new "renders\Fable-Return-2.mp4" -u "https://youtu.be/XXXXXXXXXXX" -p "Anthropic & Claude" -d "2026-07-09"
```

### Make a post from a script file (faster, cheaper, no transcription)
```
python blog_generator.py new "scripts\fable-return.txt" -u "https://youtu.be/XXXXXXXXXXX" -p "Anthropic & Claude"
```

### Flags
| Flag | Meaning |
|------|---------|
| `-u / --youtube` | YouTube URL or 11-char ID (embeds the video + pulls the thumbnail) |
| `-p / --pillar`  | Content pillar — e.g. `"The Musk AI Empire"`, `"Anthropic & Claude"`, `"Physical AI"`, `"AI Arms Race"`, `"AI Tools & Tutorials"` |
| `-d / --date`    | Publish date: `YYYY-MM-DD` or `"July 9, 2026"`. **Leave blank for today. Use it for backdating already-live videos to their real date.** |
| `-t / --title`   | Force an exact title (otherwise the AI writes an SEO one) |
| `-s / --slug`    | Force the URL slug (otherwise derived from the title) |

### Preview before publishing
```
python -m http.server 8000 --directory site
```
Open `http://localhost:8000/blog/` and eyeball the new post.

### Publish (push live)
```
python blog_generator.py publish -m "Add Fable 5 return post"
```
GitHub Pages rebuilds in ~1 minute. *(This is the automation hook — once you
trust the workflow, we can have `new` call `publish` automatically so a post
goes out with zero extra steps.)*

### Other commands
```
python blog_generator.py list       # show all posts
python blog_generator.py rebuild    # regenerate the blog index from the manifest
```

---

## THE CATCH-UP PLAN (backdating)

To catch the blog up to the channel's existing library, run `new` once per
already-live video with `-d` set to that video's **original** publish date. Each
post carries its real date, so the archive reads as naturally built over time
instead of dumped in one afternoon. After you're caught up, new posts go out
alongside each YouTube upload.

Suggested order — start with the best long-form performers (they're the ones
most likely to pull search traffic):
1. Fable 5 shutdown (best retention on the channel)
2. SpaceX IPO
3. Newsom / Anthropic (AI Arms Race Part 1)
4. Gemini Omni, ElevenLabs, HeyGen tutorials
5. …then the rest

---

## NOTES & GUARDRAILS

- **Originals are never touched.** The tool only writes into `site/blog/`.
- **The MX records are sacred.** Nothing in this setup changes email. If email
  ever hiccups, it's not this — but the fix is always "restore the MX records."
- **Posts are editable.** Every post is a plain HTML file in `site/blog/posts/`.
  Edit by hand anytime, then `rebuild` if you changed a title/date.
- **The AI can be wrong.** Skim each generated post before publishing — same as
  you'd proof a script. It's tuned to stay accurate and centrist, but you're the
  editor.
- **Model note:** uses `gemini-2.5-flash` on your billing-enabled project (the
  free tier will rate-limit on long videos — same lesson as the B-Roll Manager).

---

*Built with Axiom · Magruder Media · The AI Lab Report*
