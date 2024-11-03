#!/usr/bin/env sh

uvicorn dsw_seed_maker:app --reload --proxy-headers --forwarded-allow-ips=* --host 0.0.0.0 --port 8000
