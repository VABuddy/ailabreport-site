# Controlled Phase 1 release preparation

No deployment is authorized. Preserve the existing generator and source template.

1. Run the existing generator against this source tree using AILAB_SITE_ROOT.
2. After an approved article/manifest/archive update, run `python tools/build_release.py`.
3. Revalidate the release; sitemap should contain manifest articles plus home/archive.
4. For a local review, use `--output <new-directory> --preview`. This strips all GA tags
   and adds noindex. Serve only on 127.0.0.1. Never publish a preview directory.
5. A public artifact uses `--output <new-directory>` without `--preview`. Its explicit
   allowlist preserves known legacy pages and redirects while excluding source templates,
   drafts, documentation, deprecated manifest and tools. Add approved new public assets
   or redirects deliberately to tools/public-release.json; unknown files fail exclusion.
6. Existing branch-based Jekyll hosting must honor `_config.yml` excludes. Verify the
   current Pages build mode and inspect its artifact before any authorized deployment.
   A pipeline bypassing Jekyll must use the allowlist artifact, never the source tree.
7. Google Analytics ownership remains unverified. The homepage correction and shared
   production-host guard are prepared separately in the review packet, not applied here.

No CMS, hosting, account permission or generator API changes are involved.
