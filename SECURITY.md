# Security Policy

## Supported versions

Security fixes are applied to the latest tagged release line and the default branch (`main`), subject to maintainer capacity.

| Version   | Supported |
| --------- | --------- |
| 0.2.x     | Yes       |
| 0.1.x     | Best effort (upgrade recommended) |
| Older     | No        |

## Reporting a vulnerability

**Do not** open a public issue for undisclosed security problems.

1. Open a [GitHub Security Advisory](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) for this repository, or
2. Contact maintainers through a private channel if one is published in the repository README or organization profile.

Include: affected component (portal, pipeline, CI, release artifacts), reproduction steps, and impact assessment if known.

## Response targets (best effort)

These are goals, not SLAs.

| Severity | Examples | Target first response |
| -------- | -------- | --------------------- |
| Critical | RCE, secret exfiltration from CI, tampered release artifacts | 24 hours |
| High     | Authentication bypass, persistent XSS in portal | 72 hours |
| Medium   | Denial of service, information disclosure with limited scope | 7 days |
| Low      | Hardening, dependency advisories without exploit path | Next dependency cycle |

## Disclosure

We coordinate disclosure after a fix is available or a agreed timeline expires. Credit reporters in release notes when they wish to be named.

## Scope

In scope: code in this repository, GitHub Actions workflows configured here, and published release assets produced by those workflows.

Out of scope: third-party papers, upstream Lean/mathlib, and hypothetical attacks without a practical path against a maintained release.

## Dependency updates

Routine dependency updates are automated via Dependabot (see `.github/dependabot.yml`). Security-relevant upgrades may be prioritized out of band.
