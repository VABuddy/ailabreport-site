# AI Lab Report — controlled blog workflow

The blog is for confirmed long-form YouTube episodes only. Shorts must not receive automatically generated companion articles.

## Authoritative files

- Website checkout: C:\Tools\blog-generator\site; verified remote VABuddy/ailabreport-site; main branch.
- Only authoritative manifest: site/blog/posts.json. The October 12 preparation contains 35 preserved published records plus the approved Mistral article (36 total).
- site/posts.json is a preserved deprecated pre-release 35-entry snapshot. It is not current content data; do not edit it or use it to rebuild the listing. site/manifest-authority.json records its status.
- Canonical article directory: site/blog/posts; maintained template: site/templates/post_template.html; shared styling: site/assets/style.css.
- Original root posts copies, original template directory, and existing redirects are preserved.

## Storage and dependencies

The established C:\Tools code/checkout remains in place to preserve the existing workflow; it is an explicit operational-location exception pending an approved migration. No assets were moved. New substantial backups, drafts, tests, evidence and release reports belong under C:\MagruderMedia\AI-Lab\Production\Automation\Blog-Generator.

MAGRUDER_MEDIA_ROOT optionally configures the primary root (default C:\MagruderMedia). AILAB_SITE_ROOT explicitly configures an alternate site. AILAB_DRAFT_ROOT optionally configures drafts; its default is under the primary Magruder Media root, not C:\Tools or OneDrive. Missing authoritative content fails closed; there is no silent OneDrive fallback.

Python is sufficient for offline article JSON rendering. google-genai and existing GEMINI_API_KEY or GOOGLE_API_KEY environment configuration are needed only for separately approved Gemini calls. Never print keys. No paid calls were authorized or performed in Phases 2/3.

## Draft preparation

Run from C:\Tools\blog-generator. The default is unpublished draft output, with no manifest/index modification:

```powershell
python .\blog_generator.py new --article-json "C:\MagruderMedia\path\approved-article.json" --youtube "https://youtu.be/VALID_ID" --episode-format long-form
```

Use only an editor-confirmed long-form ID. Shorts URLs and `--episode-format short` are rejected. `--allow-api` is an additional gate requiring separate paid-generation authorization; do not add it for offline JSON.

Metadata and allowed HTML/HTTPS links are validated; JSON-LD is serialized and escaped. Existing slugs are refused, including files already present in canonical/legacy article directories. For a known forced slug, collision checking precedes any API call. Drafts have noindex/nofollow and disabled analytics. Validation does not establish factual truth; editorial source QC remains necessary.

## Local publication preparation

After explicit article approval, `--add-to-site --date YYYY-MM-DD` adds a new article, appends to the authoritative manifest, and rebuilds the listing. The date is emitted as date-only ISO metadata; this does not invent a publication hour or schedule a deployment. Existing historical timestamps remain unchanged.

The current Mistral article uses October 12, 2026 and video _uTuoUPnRuQ. Its approved article-specific direct watch fallback is present beside the 16:9 player. Do not regenerate it over the same slug; approved article revisions are deliberate edits with preserved backups.

## Publication gate

`publish` is a staging-only helper. It requires explicit `--files`, refuses outside paths/Git metadata/unrelated files/preexisting staged changes, and never commits or pushes. There is no automatic publication.

Phase 3 stopped with nothing staged. Follow the reviewed release file list, hash validation, source-status gate and rollback plan in:

C:\MagruderMedia\AI-Lab\Production\Automation\Blog-Generator\Phase-03-2026-10-12

Jeremy's final authorization is required before staging/committing/pushing/deployment. Recheck the official weights/license table and release ETA immediately before that later authorized action. Flag substantive changes rather than silently revising approved content.

The Phase 3 local preview uses a separate localhost-only release snapshot. It contains no Git metadata or credentials. It is not an external deployment.

## Preserved history

Verified pre-integration backups are under Phase-03-2026-10-12/backups. Earlier development/review drafts remain in Phase-02. Execution helper scripts are historical evidence, not future installation runners. Restore only the explicitly listed files or revert a future isolated release commit after authorization; never broadly reset or delete the checkout.

The website-wide SEO, visuals, newsletter conversion and automation audit remains a separate future project. This release makes no unrelated article edits, CSS redesign, analytics change, DNS change or account change.
