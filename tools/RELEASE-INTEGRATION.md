# Integrated release — STOP before deployment

Baseline: 408e030aa03f69175a69f3d9dee8a5722de1115f; production and live manifest contain 36 articles. Run #5 is excluded.

Run the installed blog generator only against an isolated AILAB_SITE_ROOT. Drafts must remain in a separate AILAB_DRAFT_ROOT; never add Run #5 to the manifest without approval.
After an approved publication, run `python tools/build_release.py --site <isolated-source> --output <NEW-output-directory> --as-of YYYY-MM-DD`.
The build refreshes the feature from tools/public-content.json, normalizes only generated archive cards, refreshes discovery files, validates metadata and rejects unknown files exposed by legacy Pages. It never invokes API generation, Git publication, or deployment.
Register new long-form episodes with editorial approval and fresh public evidence in the ledger. Manifest additions alone do not grant feature eligibility. The template remains the approved homepage composition; no hand-editing the rendered feature.
For local previews add --preview. Preview robots/noindex and stripped analytics are never release source.

Verified Pages configuration: legacy build, main branch, repository root, HTTPS enforced. _config.yml exclusions govern this real production route. The offline artifact's .nojekyll is diagnostic packaging only; it is not added to the repository source.

Final build verification now uses pinned Ruby 3.3.4, github-pages 232 and Jekyll 3.10.0. The actual Pages artifact matches all 81 accepted public payload files byte for byte; the offline .nojekyll packaging marker is intentionally absent. The default Primer theme is disabled with theme: null to avoid an unused generated CSS file. Full method, lockfile, exclusion canaries, manifest and test evidence are retained in the sibling Final-Build-Verification workspace. Technical GO is subject to final review; production deployment remains unauthorized.
Before any future approved deployment, compare remote HEAD and both manifests again, reconcile all newer articles, verify the feature remains public, build/test again, review exact changed files and freeze hashes. Do not use the installed generator publish allowlist for this broader release; do not broaden it silently.
Stage only reviewed changed paths in the correct production repository after Jeremy authorizes the release. A commit/push to main triggers production Pages and therefore requires explicit deployment authorization. No such action has been taken.
Rollback must revert only the future integration commit/diff, reconcile conflicts against later blog releases, preserve manifests/article bodies/new URLs, rebuild and inspect the prior approved public artifact. Never reset main to the historical baseline. Rollback also needs authorization.

Rollback clarification: keep the verified template/tools/draft exclusions active when restoring older visual components. Reconcile later articles and manifests, build with the pinned engine, and inspect the resulting artifact before any separately authorized rollback deployment.
