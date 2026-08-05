# AGENTS.md

Security/observability repo: a collection of standalone projects. The actively developed one is `Manum/`; most other top-level dirs (`retired_pocs/`, `Exploits/`, `SIEM/`, `MITM-Project/`, `Facial_Recognition/`, `FFI/`, `signature authentication/`, `TinFoilHat/`) are separate experiments with their own tooling — don't assume shared structure.

## Manum (`Manum/`)

Monitoring stack (M-A-N-U-M): **ClickHouse** (indexer) + **Vector** (forwarder/agent) + **Grafana** (dashboard), orchestrated with the docker SDK by `deploy.py`.

- Deploy: `sudo python3 deploy.py --migrate --indexer --dashboard --forwarder` from inside `Manum/` (`deploy.py` uses `os.getcwd()` as `base_dir`). Add `--test` to use `test.json` instead of `settings.json` and skip starting Vector.
- **`deploy.py` is destructive**: it kills and removes every container and network whose name contains the `name` from `settings.json` (`MANUM`) before recreating them. Rerunning wipes/rebuilds everything.
- Requires `python-docker` (`docker.from_env()`), a running docker daemon, and `sudo`.

### Components (`Manum/Components/<Name>/`)

Each component has:
- `<Name>.sql` — ClickHouse DDL; all components' SQL is concatenated in directory order and run as one migration (`clickhouse-client --multiquery`).
- `<Name>.toml` — **not raw TOML**: it is a Python f-string (starts with `f"""`) that `deploy.py` `eval()`s with `settings.json` loaded as `data`. Escape literal braces as `{{ }}`. Refer to values like `data["forwarder"]["BasicMetrics"]["port"]`.
- `Agent.toml` (optional) — collector-side Vector config, same f-string pattern but uses the `data["agent"]` section.

The `forwarder`/`agent` sections of `settings.json` define which ports, unix sockets (`unix_sockets/`), log dirs (`logs/`), and TLS certs (`cert/`) get mounted into containers. The `cert/` dir contains `cert.pem`/`key.pem` used for TLS sources (e.g. `FE_profiling` on 443).

### process_pulse.c

C binary that scrapes `/proc` for system/process metrics and sends JSON chunks (framed with `<start>`/`<end>` markers) over a **UNIX datagram socket** at `/tmp/processes.sock`. Replaces the deleted `newProc.c`. Build with plain `gcc -O2 -o process_pulse process_pulse.c` (no external deps). When wiring it to a Vector component, verify the socket path against the component's `Agent.toml` (`/tmp/unix_sockets/...`) — they currently differ.

### Other files

- `s3-sync.py` — pulls files from `s3://<bucket>/<path>/YYYY/MM/DD/` newer than 6h, deletes local files older than 6h. Needs `boto3` + AWS creds.
- `Dashboards/*.json` — exported Grafana dashboards; `backup.db` is the Grafana SQLite DB mounted into the dashboard container.
- `settings.json` = live config with **real credentials** (ClickHouse/Grafana passwords, AWS Redis host) and is committed. `test.json` is the localhost test variant (JSONC with comments). Don't print these creds into diffs or logs.

## CI (`.gitlab-ci.yml`)

GitLab CI runs: trufflehog (verified-secrets scan, fails on push), semgrep (`auto`/`p/python`/`p/security-audit` on main/MR), sonarqube (needs `SONAR_HOST_URL`/`SONAR_TOKEN` GitLab variables), and a Python self-test that runs `python3 selftest.py` — **`selftest.py` does not exist** in the repo (only a no-op `test.py`); don't create it unless asked.

## Root misc

- `package.json` (`name: pipeline`) references a `pipeline.js` that does not exist.
- `Notes.js` at root is a reference scratch file for a loadboard API/SQL audit — not code to run.
- `.gitignore` only excludes `node_modules/`, `NodeGoat/`, `/api_gateway/.env`.
