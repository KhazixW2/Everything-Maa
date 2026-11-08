# Release process

Everything Maa is not published yet. This checklist prepares a release without storing registry tokens in the repository.

## One-time setup

1. Create the public `KhazixW2/Everything-Maa` GitHub repository and add it as this checkout's remote.
2. Confirm that the unscoped npm name `everything-maa` is available to the intended publisher.
3. Publish the first version manually after `main` is public, because npm requires the package to exist before a trusted publisher can be attached:

```bash
npm login
npm publish
```

4. In the npm package settings, configure GitHub Actions as the trusted publisher:
   - owner: `KhazixW2`;
   - repository: `Everything-Maa`;
   - workflow filename: `release.yml`;
   - allowed action: npm publish.
5. Protect the default branch and release tags. Optionally attach an approval-protected GitHub environment before enabling public releases.

Trusted publishing requires a public GitHub-hosted workflow with OIDC. The release workflow uses Node.js 24 and grants `id-token: write`; it does not require an `NPM_TOKEN` secret.

## Prepare a version

1. Move the relevant entries from `Unreleased` into a dated version section in `CHANGELOG.md`.
2. Set the same semantic version in:
   - `package.json` and `package-lock.json`;
   - `.codex-plugin/plugin.json`;
   - `.claude-plugin/plugin.json`;
   - `.claude-plugin/marketplace.json`;
   - `distribution/catalog.json`.
3. Review third-party version policies and licenses in `mcp/catalog.json`, `integrations/catalog.json`, and `THIRD_PARTY_NOTICES.md`; create-maa-project and MaaEvidenceKit track latest.
4. Run:

```bash
uv sync
uv run python -m pytest
uv run python scripts/validate_skills.py
npm test
npm run release:check
npm run smoke:create-project
npm run smoke:maafw-cli
```

5. Inspect `npm pack --dry-run` and test the resulting tarball through `npx` before tagging.

## Publish

Create and push an annotated `vX.Y.Z` tag only after the version commit is on the protected default branch. The tag must exactly match `package.json`.

The Release workflow re-runs validation, creates the tarball, publishes an unpublished version through npm trusted publishing, and then creates a GitHub Release with that exact tarball. If the version already exists because it was the manual bootstrap release, the workflow skips the duplicate npm publish and still creates the GitHub Release. A manual workflow dispatch builds and uploads the artifact but deliberately does not publish.

After the workflow completes, verify the npm provenance link, GitHub Release asset, clean-install behavior for Codex and Claude Code, and the documented install commands. Do not mark a release complete if any distribution surface reports a different version.
