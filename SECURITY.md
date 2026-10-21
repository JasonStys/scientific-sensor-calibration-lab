# Security policy

Offline single-user synthetic calibration education. Not Internet-hardened, an account service, a device controller or a safety/certification instrument. Do not proxy/bind it publicly or enter confidential facility data. No uploads, credentials, accounts, advertisements, analytics, remote fonts/scripts, AI APIs or network data connectors are included.

Strict input boundaries: exact types/ranges/schema, no duplicate keys, UTF-8≤64KiB, limited record counts, no executable input. A fixed trusted C# worker receives bounded JSON without a shell; timeout/nonfinite/malformed output fails closed against an independent reference. The worker itself has a second parser boundary. Users with OS access can replace binaries/files; content hashes are not signatures or a sandbox.

HTTP binds only IPv4 loopback, enforces Host/Origin/fetch metadata, has no CORS/mutation, confines built assets and emits CSP/no-frame/nosniff/no-referrer/no-store headers. Report strings become text or escaped inert HTML; failed/stale requests hide evidence. The standard-library threaded HTTP server is not a denial-of-service defense against hostile local processes. SQL history uses bound parameters, verified identity, immutable triggers and no automatic pruning; it is unencrypted and OS-level modification is still possible.

Build protection includes pinned stable SDK, locked/hash-verified dependencies, SHA-pinned least-privilege Actions, no persisted checkout credentials, disabled caching/uploads and three-language CodeQL plus dependency audits. Future vulnerabilities may exist despite current audits. Portable releases include runtime notices and are unsigned. Verify source/checksums and platform policy; do not bypass security warnings. Runtime/private data and build outputs are ignored by Git.

Report suspected issues privately using GitHub private vulnerability reporting if available, or contact Jason Stys through his GitHub profile without publicly posting sensitive details, credentials or real facility records. Do not attach private account/storage archives to public issues.
