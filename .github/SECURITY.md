# Security Policy

BudgetApp is currently **proprietary / all rights reserved** (see SPEC.md §8).
The project is not yet released publicly, but we take security reports
seriously at every stage of development.

## Reporting a vulnerability

**Please do not open public issues, discussions, or pull requests for security
vulnerabilities.** Public disclosure before a fix is in place puts every
self-hosted household finance instance at risk.

Report privately via one of the following:

1. **GitHub Private Vulnerability Reporting.** On this repository, go to the
   "Security" tab and choose "Report a vulnerability". This opens a private
   thread visible only to the repo owner and the reporter.
2. **Direct contact with the repo owner** (`@croogmandoo`) if private
   reporting is unavailable to you.

When you report, please include:

- A description of the vulnerability and the component it affects.
- Reproduction steps, a proof of concept, or a minimal failing example.
- The version / commit SHA you tested against.
- Any suggested remediation, if you have one.

## What to expect

- We will acknowledge receipt within a few business days.
- We will work with you on a fix and a coordinated disclosure timeline.
- We will credit you in the release notes for the fix unless you prefer to
  remain anonymous.

## Scope

In scope for a security report:

- Authentication, authorization, session handling, TOTP / MFA flows.
- Data-at-rest encryption (envelope encryption, DEK handling, attachment
  encryption, backup encryption).
- Injection (SQL, command, template) and XSS / CSRF.
- Insecure dependencies shipped in our Docker images.
- Webhook signing / verification issues.
- Audit-log tampering or gaps for state-changing actions.

Out of scope (see SPEC.md §7.6 threat model):

- Host-level compromise of the server running BudgetApp. Because the master
  key lives in an environment variable by design, root on the host equals
  data compromise. This is an accepted, documented trade-off.
- Denial-of-service that requires pre-authenticated privileged access.
- Reports from automated scanners without a demonstrated exploit.

## Supported versions

The project is pre-v1. Until the first tagged release, only `main` receives
security fixes. After v1, this section will list the supported version
ranges.
