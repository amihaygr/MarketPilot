# Database

Place versioned MariaDB migrations and safe seed data here.

Initial planned objects are documented in `docs/architecture/architecture.md`.

Requirements:

- explicit primary and unique keys;
- idempotent migrations where practical;
- separate API and ingestion identities;
- indexes driven by verified query patterns;
- no real data dumps in Git.
