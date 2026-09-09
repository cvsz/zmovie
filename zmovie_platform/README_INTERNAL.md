# zMovie Platform Internals

See the [documentation index](../docs/INDEX.md) for canonical guides and
cross-component procedures.

This package contains the v2 production domain, persistence, providers, storyboard, QC, render orchestration, media assembly, authentication, and export modules. `main:app` is the composed HTTP entry point; `app.py` retains the legacy prompt implementation and `zmovie.py` remains backward-compatible as the standalone prompt generator.
