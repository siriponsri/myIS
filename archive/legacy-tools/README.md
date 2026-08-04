# Legacy Tools

This directory preserves retired repository utilities for provenance. Files
here are historical, are not active runtime entry points, and must not be
imported by current code or used as execution authority.

`build_migration_manifest.py` was retired during the ArmIndex closeout because
it had no active caller and emitted personal absolute roots, which are not
permitted in repository-safe migration artifacts.
