#!/usr/bin/env python3
r"""
The AI Lab Report — Blog Generator
==================================
Turns a finished video (HeyGen render) OR a script .txt into a polished,
on-brand blog post for theailabreport.com — same spirit as the B-Roll Manager.

Uses the Gemini API (reuse the same key/billing project as broll-manager;
model gemini-2.5-flash). Gemini reads audio/video natively, so you can feed
it the HeyGen render directly — it transcribes what you actually said, then
writes the post.

COMMANDS
--------
  new <input>        Generate a post from a video/audio file OR a .txt script.
  rebuild            Regenerate the blog index from the posts manifest.
  list               List all posts currently in the manifest.
  publish            Commit + push the site to GitHub (the automation path).

EXAMPLES
--------
  # From the HeyGen render (Gemini transcribes it):
  python blog_generator.py new "renders\Fable-Return-2.mp4" ^
      --youtube "https://youtu.be/XXXXXXXXXXX" ^
      --pillar "Anthropic & Claude" ^
      --date "2026-07-09"

  # From a clean script file (faster / cheaper, no transcription):
  python blog_generator.py new "scripts\fable-return.txt" ^
      --youtube "https://youtu.be/XXXXXXXXXXX" --pillar "Anthropic & Claude"

  # Backdating an already-live video to its original publish date:
  python blog_generator.py new "scripts\spacex-ipo.txt" ^
      -u "https://youtu.be/58GokwlQ6oE" -p "The Musk AI Empire" -d "2026-06-10"

  python blog_generator.py list
  python blog_generator.py publish -m "Add Fable 5 return post"

SETUP: see README.md.
"""

import os
import re
import sys
import json
import time
import argparse
import datetime
import subprocess

# ----------------------------------------------------------------------
# Paths / config
# ----------------------------------------------------------------------
HERE      = os.path.dirname(os.path.abspath(__file__))
SITE      = os.path.join(HERE, "site")
POSTS_DIR = os.path.join(SITE, "blog", "posts")
MANIFEST  = os.path.join(SITE, "blog", "posts.json")
TEMPLATE  = os.path.join(HERE, "templates", "post_template.html")
INDEX     = os.path.join(SITE, "blog", "index.html")

MODEL = "gemini-2.5-flash"   # billing-enabled project — NOT 2.0-flash (see B-Roll Manager notes)

# Pillars whose tag renders in blue instead of the default cyan
BLUE_PILLARS = {"the musk ai empire", "physical ai"}

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}

KIT_LINK = "https://the-ai-lab-report.kit.com/ecbaa90629"


# ----------------------------------------------------------------------
# Gemini client
# ----------------------------------------------------------------------
def get_model():
    """Load the Gemini client. Reuses GEMINI_API_KEY from the environment
    (same key as broll-manager)."""
    try:
        import google.generativeai as genai
    except ImportError:
        sys.exit("Missing dependency. Run:  pip install google-generativeai")

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        sys.exit(
            "No API key found. Set GEMINI_API_KEY in your environment\n"
            "(the same key the B-Roll Manager uses). For example, in PowerShell:\n"
            '    setx GEMINI_API_KEY "your-key-here"\n'
            "then open a new terminal."
        )
    genai.configure(api_key=key)
    return genai


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:70].strip("-")


def extract_youtube_id(url_or_id):
    if not url_or_id:
        return ""
    s = url_or_id.strip()
    # already an ID
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    m = re.search(r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})", s)
    return m.group(1) if m else ""


def parse_date(s):
    """Return (display_date, iso_date, sort_key) from a flexible date string.
    Accepts '2026-07-09', 'July 9, 2026', or blank (=today)."""
    if not s:
        d = datetime.date.today()
    else:
        s = s.strip()
        d = None
        for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%m/%d/%Y"):
            try:
                d = datetime.datetime.strptime(s, fmt).date()
                break
            except ValueError:
                continue
        if d is None:
            sys.exit(f"Couldn't parse date '{s}'. Use YYYY-MM-DD or 'July 9, 2026'.")
    display = d.strftime("%B %-d, %Y") if os.name != "nt" else d.strftime("%B ") + str(d.day) + d.strftime(", %Y")
    iso = d.strftime("%Y-%m-%dT15:00:00-04:00")   # default 3PM ET publish slot
    return display, iso, d.strftime("%Y-%m-%d")


def tag_class_for(pillar):
    return "blue" if pillar.strip().lower() in BLUE_PILLARS else ""


# ----------------------------------------------------------------------
# The core generation prompt
# ----------------------------------------------------------------------
def build_prompt(pillar, forced_title, source_note):
    title_line = (
        f'Use this exact title: "{forced_title}".'
        if forced_title else
        "Write a strong, specific, curiosity-driven SEO title (aim for the 3-second test: "
        "a stranger should instantly know what they're getting). Avoid clickbait that "
        "the post doesn't deliver on."
    )
    return f"""You are the writer for THE AI LAB REPORT, a breaking-AI-news YouTube channel and blog.
{source_note}

Turn this into a polished BLOG POST — not a transcript. Rewrite it as an article a reader
would read, not a script someone would speak. Keep the channel's voice:
- Editorial and opinionated, with a clear point of view and a strong close.
- Sharp but fair. CENTRIST on politics — apply skepticism evenhandedly, never partisan.
- Direct address to the reader ("you"), light humor, rhetorical tension.
- Accurate. Do NOT invent quotes from real people or fabricate specific numbers/dates
  that aren't supported by the source. When unsure, stay general.

Content pillar: {pillar}
{title_line}

Return ONLY a JSON object (no markdown fences, no preamble) with these exact keys:
{{
  "title": "the post title",
  "meta_description": "155-char max SEO meta description",
  "dek": "one punchy sentence (the standfirst under the title), ~20-30 words",
  "slug": "url-slug-lowercase-hyphens",
  "body_html": "the article body as clean semantic HTML using ONLY <p>, <h2>, <h3>, <blockquote>, <ul>, <li>, <strong>, <em>, and <a href> tags. 700-1100 words. Open with a hook paragraph. Use 3-5 <h2> sections. Include one <blockquote> pull-quote. End with a 'why this matters to you' beat. Do NOT include the title, the video, the CTA, or the footer — only the article body.",
  "cta_eyebrow": "short label for the email CTA (e.g. 'Stay ahead of the story' for news, 'Free download' for tutorials)",
  "cta_heading": "the CTA headline",
  "cta_text": "1-2 sentences pitching the newsletter, matched to this post's topic",
  "cta_button": "button label (e.g. 'Join the newsletter' or 'Get the free PDF')",
  "tools_note": "a short closing HTML line (<p>...</p>) linking to the YouTube channel and inviting a subscribe. For tutorial posts, this is where affiliate tool links go, formatted as <a href> tags with a disclosure that they're affiliate links."
}}"""


def call_gemini(genai, input_path, pillar, forced_title):
    model = genai.GenerativeModel(MODEL)
    ext = os.path.splitext(input_path)[1].lower()

    parts = []
    if ext in VIDEO_EXTS or ext in AUDIO_EXTS:
        print(f"  Uploading {os.path.basename(input_path)} to Gemini (this can take a minute for long videos)...")
        f = genai.upload_file(path=input_path)
        # wait for processing
        while f.state.name == "PROCESSING":
            time.sleep(3)
            f = genai.get_file(f.name)
        if f.state.name == "FAILED":
            sys.exit("Gemini failed to process the media file.")
        source_note = ("The source is the FINISHED VIDEO for an episode. Transcribe what is "
                       "actually said, then write the post from that — capture the real content, "
                       "including anything ad-libbed beyond the script.")
        parts = [f, build_prompt(pillar, forced_title, source_note)]
    elif ext in {".txt", ".md"}:
        with open(input_path, "r", encoding="utf-8") as fh:
            script = fh.read()
        source_note = "The source is the SCRIPT for an episode, below:\n\n" + script
        parts = [build_prompt(pillar, forced_title, source_note)]
    else:
        sys.exit(f"Unsupported input type '{ext}'. Use a video, audio, or .txt file.")

    print("  Writing the post with Gemini...")
    resp = model.generate_content(parts, generation_config={"temperature": 0.7})
    raw = resp.text.strip()
    # strip accidental code fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # last-ditch: pull the outermost {...}
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        sys.exit("Gemini didn't return valid JSON. Re-run, or paste a cleaner script.")


# ----------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------
def render_post(data, youtube_id, display_date, iso_date, pillar):
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        tpl = f.read()
    repl = {
        "TITLE": data["title"],
        "META_DESCRIPTION": data["meta_description"].replace('"', "'"),
        "DEK": data["dek"],
        "SLUG": data["slug"],
        "BODY": data["body_html"],
        "YOUTUBE_ID": youtube_id,
        "PILLAR": pillar,
        "TAG_CLASS": tag_class_for(pillar),
        "DISPLAY_DATE": display_date,
        "ISO_DATE": iso_date,
        "CTA_EYEBROW": data.get("cta_eyebrow", "Stay ahead of the story"),
        "CTA_HEADING": data.get("cta_heading", "Get the breakdowns before the noise catches up"),
        "CTA_TEXT": data.get("cta_text", "The AI stories that matter, decoded and sent straight to you."),
        "CTA_BUTTON": data.get("cta_button", "Join the newsletter"),
        "TOOLS_NOTE": data.get("tools_note", ""),
    }
    for k, v in repl.items():
        tpl = tpl.replace("{{" + k + "}}", str(v))
    return tpl


def rebuild_index():
    """Regenerate the blog index card list from the manifest."""
    posts = load_manifest()
    posts.sort(key=lambda p: p.get("sort_key", ""), reverse=True)
    cards = []
    for p in posts:
        thumb = (f'<img src="https://i.ytimg.com/vi/{p["youtube_id"]}/hqdefault.jpg" '
                 f'alt="{p["title"]}" loading="lazy">') if p.get("youtube_id") else ""
        tagcls = p.get("tag_class", "")
        cards.append(f"""    <a class="post-card" href="/blog/posts/{p['slug']}.html">
      <div class="thumb">{thumb}</div>
      <div class="body">
        <div class="meta"><span class="tag {tagcls}">{p['pillar']}</span><span class="date">{p['display_date']}</span></div>
        <h3>{p['title']}</h3>
        <p>{p['dek']}</p>
        <div class="readmore">Read the breakdown &rarr;</div>
      </div>
    </a>""")
    block = "\n".join(cards)
    with open(INDEX, "r", encoding="utf-8") as f:
        html = f.read()
    html = re.sub(r"<!-- POSTS_START -->.*<!-- POSTS_END -->",
                  "<!-- POSTS_START -->\n" + block + "\n    <!-- POSTS_END -->",
                  html, flags=re.DOTALL)
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)


def load_manifest():
    if not os.path.exists(MANIFEST):
        return []
    with open(MANIFEST, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(posts):
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2)


# ----------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------
def cmd_new(args):
    if not os.path.exists(args.input):
        sys.exit(f"Input not found: {args.input}")
    youtube_id = extract_youtube_id(args.youtube)
    if not youtube_id:
        print("  ! No valid YouTube ID/URL given — the post will be created with an empty embed.")
        print("    Pass --youtube once the video is live, or edit the post file later.")
    display_date, iso_date, sort_key = parse_date(args.date)

    genai = get_model()
    print(f"Generating post from: {os.path.basename(args.input)}")
    data = call_gemini(genai, args.input, args.pillar, args.title)
    if args.slug:
        data["slug"] = slugify(args.slug)
    else:
        data["slug"] = slugify(data.get("slug") or data["title"])

    html = render_post(data, youtube_id, display_date, iso_date, args.pillar)
    out_path = os.path.join(POSTS_DIR, data["slug"] + ".html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    # update manifest (replace if slug exists)
    posts = [p for p in load_manifest() if p.get("slug") != data["slug"]]
    posts.append({
        "slug": data["slug"], "title": data["title"], "dek": data["dek"],
        "pillar": args.pillar, "tag_class": tag_class_for(args.pillar),
        "youtube_id": youtube_id, "display_date": display_date,
        "iso_date": iso_date, "sort_key": sort_key,
    })
    save_manifest(posts)
    rebuild_index()

    print(f"\n  Created: site/blog/posts/{data['slug']}.html")
    print(f"  Title:   {data['title']}")
    print(f"  Date:    {display_date}")
    print(f"  Index rebuilt ({len(posts)} post(s) total).")
    print("\n  Preview locally:  python -m http.server 8000 --directory site")
    print("  then open http://localhost:8000/blog/")
    print("  When it looks right:  python blog_generator.py publish")


def cmd_rebuild(args):
    rebuild_index()
    print(f"Index rebuilt from manifest ({len(load_manifest())} posts).")


def cmd_list(args):
    posts = sorted(load_manifest(), key=lambda p: p.get("sort_key", ""), reverse=True)
    if not posts:
        print("No posts yet.")
        return
    print(f"{len(posts)} post(s):\n")
    for p in posts:
        print(f"  {p['display_date']:>16}  [{p['pillar']}]")
        print(f"                    {p['title']}")
        print(f"                    /blog/posts/{p['slug']}.html\n")


def cmd_publish(args):
    """Commit + push the site. This is the automation path — once you're happy
    with the workflow, `new` can call this for you automatically."""
    msg = args.message or f"Update blog ({datetime.date.today().isoformat()})"
    try:
        subprocess.run(["git", "-C", HERE, "add", "-A"], check=True)
        subprocess.run(["git", "-C", HERE, "commit", "-m", msg], check=True)
        subprocess.run(["git", "-C", HERE, "push"], check=True)
        print("Pushed. GitHub Pages will rebuild in ~1 minute.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"Git step failed: {e}\nIs this folder a git repo with a remote set? See README.md.")


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="The AI Lab Report — Blog Generator")
    sub = ap.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="Generate a post from a video/audio file or .txt script")
    p_new.add_argument("input", help="Path to a video, audio, or .txt script")
    p_new.add_argument("-u", "--youtube", default="", help="YouTube URL or 11-char video ID")
    p_new.add_argument("-p", "--pillar", default="AI News & Analysis",
                       help="Content pillar (e.g. 'Anthropic & Claude', 'The Musk AI Empire', 'Physical AI')")
    p_new.add_argument("-t", "--title", default="", help="Force an exact title (optional; AI writes one otherwise)")
    p_new.add_argument("-d", "--date", default="", help="Publish date: YYYY-MM-DD or 'July 9, 2026' (blank=today). Use for backdating.")
    p_new.add_argument("-s", "--slug", default="", help="Force the URL slug (optional)")
    p_new.set_defaults(func=cmd_new)

    p_rb = sub.add_parser("rebuild", help="Rebuild the blog index from the manifest")
    p_rb.set_defaults(func=cmd_rebuild)

    p_ls = sub.add_parser("list", help="List all posts")
    p_ls.set_defaults(func=cmd_list)

    p_pub = sub.add_parser("publish", help="Commit + push the site to GitHub")
    p_pub.add_argument("-m", "--message", default="", help="Commit message")
    p_pub.set_defaults(func=cmd_publish)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
