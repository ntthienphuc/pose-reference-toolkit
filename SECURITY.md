# Security scope

This is a local research/demo server, not a hardened public upload service. Defaults bind to loopback. Never load untrusted legacy pickled banks; this package's NPZ loaders disable pickle. Restrict access and apply service-level request, concurrency and storage controls if exposing the API.

The bank's hashes detect modifications relative to its manifest and loaded version; they do not authenticate the publisher. The source manifest's permission and identity fields are operator declarations. Report reproducible defects without posting private recordings, credentials or weaponized inputs in public issues.
