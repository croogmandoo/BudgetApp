<!--
Thanks for the change. Fill every section; tick every box in the security
checklist or mark the box with "(N/A) <short reason>".
-->

## Summary

<!-- What does this change do, and why? Keep it tight. -->

## Type of change

- [ ] Feature
- [ ] Fix
- [ ] Refactor
- [ ] Docs
- [ ] Chore
- [ ] Security

## Spec reference

Links to SPEC.md section(s) affected:

<!-- e.g. SPEC.md §3.1 (Accounts & Transactions), §7.2 (Data at Rest) -->

## Test plan

<!-- How did you validate the change? Commands run, scenarios covered,
     migrations exercised, manual steps, screenshots if UI. -->

## Security checklist

All must be ticked or explicitly marked N/A with a reason.

- [ ] No secrets, tokens, or private keys added to the repo.
- [ ] Input validation added at API boundaries for new endpoints.
- [ ] Authentication/authorization reviewed for new endpoints.
- [ ] No new SQL/NoSQL query built by string interpolation.
- [ ] New dependencies reviewed for licence and vulnerability posture.
- [ ] No logging of PII, tokens, or sensitive financial data.
- [ ] Audit log coverage considered for state-changing actions (see SPEC §7.5).

## Breaking changes

- [ ] Yes
- [ ] No

<!-- If yes, describe the break, the migration path, and any required
     operator action (env vars, backup steps, schema migrations). -->
