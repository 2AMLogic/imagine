# Work Log

Chronological record of merged PRs and closed issues, maintained by the Guide role.

### 2026-11-16

- **PR #44**: fix: hash fit source before fit_image writes dest
- **Issue #37** (closed): fit: in-place fit (-o pointing at the source) records a self-referential source_sha256
- **PR #17**: docs: roadmap as of 2026-11-13
- **PR #46**: tests: hoist duplicated cli.fit_image double into shared conftest fixtures
- **Issue #43** (closed): tests: hoist the duplicated cli.fit_image double into a shared conftest fixture
- **PR #36**: fix: print --json records to stdout; stderr stays diagnostics-only
- **Issue #31** (closed): gen/edit: --json payload and applicability notes share stderr, so json.loads(stderr) breaks
- **PR #41**: tests: cover cmd_fit's default destination name and flag passthrough
- **Issue #30** (closed): tests: cover cmd_fit's default destination name (<stem>-fit.png)
- **PR #39**: fix: note --cf-account as ignored on Gemini models
- **Issue #26** (closed): gen/edit: --cf-account is silently ignored on a Gemini model
- **PR #38**: fix: flatten source alpha explicitly in contain's alpha-less letterbox (partial; Issue #33 stays open for an attended render probe)

### 2026-11-15

- **PR #35**: feat: write a provenance sidecar for fit output
- **PR #29**: fix: stop fit writing PNG bytes under a non-PNG name; add postprocess tests
- **PR #27**: fix: give gen/edit the same Cloudflare account-selection guidance as doctor
- **Issue #22** (closed): Deduplicate the Cloudflare credentials-missing hint: gen still prints the pre-#4 message
- **Issue #21** (closed): fit: write a provenance sidecar for the fitted image
- **Issue #20** (closed): fit: stop writing PNG bytes under a non-PNG name, and add tests for postprocess
- **PR #25**: feat: note on stderr when --param or --size does not apply to the provider
- **Issue #18** (closed): gen/edit: print a note when --param or --size does not apply to the selected provider

### 2026-11-14

- **PR #24**: feat: record --param values as `params` in gen/edit provenance
- **Issue #19** (closed): gen/edit: record --param values in the provenance sidecar

### 2026-11-05

- **PR #14**: docs: document opaque output and add full-bleed-then-mask transparency recipe
- **PR #13**: feat: retry transient provider errors with bounded backoff
- **PR #12**: feat: write install metadata and gitignored sidecar from install.sh
- **PR #11**: fix: doctor reports NEEDS ACCOUNT when workers-ai.env exists but no account selected
- **PR #10**: fix: write generated images under the extension their bytes require
- **PR #9**: fix: send multipart/form-data for FLUX.2 Cloudflare models
- **Issue #6** (closed): install.sh: ship install-metadata.json + local-source sidecar so imagine participates in tool discovery/update
- **Issue #5** (closed): gen: -o out.png writes provider bytes verbatim, so a .png file can contain JPEG (and the sidecar does not record the real format)
- **Issue #4** (closed): doctor: reports cloudflare MISSING when a valid workers-ai.env exists but no account is selected
- **Issue #3** (closed): gen: flux-2-dev fails with Cloudflare 400 — model requires a multipart body the CLI never sends
- **Issue #2** (closed): gen: retry transient provider errors (Gemini 503 UNAVAILABLE) instead of failing with exit 1
- **Issue #1** (closed): gen: "transparent background" prompts return baked-in checkerboard, not real alpha

### 2026-11-04

- **PR #8**: Install Loom ahead of fleet admission, with a provider-credential rule
