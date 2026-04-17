#!/usr/bin/env python3
"""Backward-compatible alias for scripts/run_seed_pipeline.py."""

import run_seed_pipeline

if __name__ == "__main__":
    raise SystemExit(run_seed_pipeline.main())
