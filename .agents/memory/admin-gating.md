---
name: Admin gating — role is source of truth
description: Why is_admin must be derived from role==admin at read time, not read from the stored column
---

# Admin gating: derive is_admin from role

`users` has BOTH a stored boolean `is_admin` AND a `role` enum (`Role.admin` = "admin").
The two can desync — e.g. a manual `UPDATE users SET role='admin'` (or aligning DEV↔PROD
by editing only `role`) leaves `is_admin=false`. Symptom: account page shows "Ruolo: admin"
but the Admin nav link is hidden and admin endpoints 403, because gating reads `is_admin`.

**Rule:** treat `role` as the single source of truth. Auth serialization
(`api/routers/auth.py` `require_user` + `login_endpoint`) computes
`is_admin = (user.role == Role.admin)` instead of reading the stored column.
`require_admin` (admin.py) consumes that derived value transitively.
`users_repo.set_role` still writes the legacy column for backward compat — harmless.

**Why:** the stored column is legacy/derivable (see model comment) and any direct DB edit
to `role` can desync it, producing "role=admin but no admin access". Deriving at read time
makes that class of bug impossible without touching data.

**How to apply:** never gate admin on the raw `is_admin` column; gate on `role == Role.admin`
(or the derived value from auth serialization). Production DB writes are NOT possible from the
main agent (prod is a read-only replica) — fix admin access via the code derive + redeploy,
not by UPDATE-ing prod data.
