# Security Policy

Report suspected credential exposure, protected-data leakage, unsafe path
handling, or read-only viewer mutation privately to the repository Owner. Do
not open a public issue containing secrets, query IDs, family IDs, qrels,
rankings, split membership, raw patent payloads, or personal absolute paths.

The Dashboard and MLflow viewer bind to loopback only. Browser requests use
allowlisted actions and may not supply commands, paths, ports, or arguments.
Persistent stores remain outside Git and must pass path, hash, and read-only
checks.

No public security response SLA is currently promised. This research repository
is not a production service and should not be exposed directly to a network.
