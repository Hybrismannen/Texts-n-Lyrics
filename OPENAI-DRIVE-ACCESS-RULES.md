# Director Policy — OpenAI Google Drive Create-Only Access

**Policy ID:** OAI-DRIVE-APPEND-ONLY-001 v1.0 (2026-11-18).
**Authoritative private source:** My Drive / `0. Open AI - Access & Privacy Rules` / https://docs.google.com/document/d/18nexuzVfOEWwM7vXcPcB1NkjQHsEGKWxZHSqo-qlBRs/edit

AI may READ task-relevant Google Drive content and CREATE genuinely NEW private documents/folders/files under approved destinations, initializing each new object only during its recorded creation transaction. All PRE-EXISTING Drive objects, including previously created outputs, are READ-ONLY by default. AI may not edit, append, overwrite, replace, move, rename, relabel, change permissions or sharing, trash, delete, purge, deduplicate, sync-away, rollback or cleanup existing files or folders without the Director's explicit, prior, exact-target-ID and exact-operation authorization. Never auto-remove temporary files. Inferred permission, broad OAuth grants, repo permissions and general instructions are insufficient; missing authority means DENY.

For every potentially destructive or modifying action, show affected Drive IDs, paths, preview/diff, rationale, reversibility and consequences; request explicit itemized Director approval; enforce a server-side pre-API gate with logging and negative tests. Do not expose private Drive material to public code or third parties. Read the full private Director policy before Drive actions. A new repo policy file/draft PR is not itself runtime enforcement or a CDX admission. Preserve any separate repository authority and governance.
