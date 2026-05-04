# SwiftDeploy

SwiftDeploy is a declarative deployment CLI tool that automatically builds and manages your entire application stack from a single `manifest.yaml` file. Instead of manually writing config files, you define what you want in the manifest and the CLI handles everything else.

## How It Works
manifest.yaml → swiftdeploy → nginx.conf + docker-compose.yml → running app
You write `manifest.yaml` once. The CLI reads it and generates all the config files needed to run your app behind an Nginx reverse proxy inside Docker containers.


## Prerequisites

- Docker Desktop installed and running
- Python 3.11 or higher
- PyYAML: `pip install pyyaml`


## Setup Instructions

**1. Clone the repo**
```bash
git clone https://github.com/DivineObido/swiftdeploy-cli.git
cd swiftdeploy-cli
```

**2. Build the Docker image**
```bash
cd app
docker build -t swift-deploy-1-node:latest .
cd ..
```

**3. Make the CLI executable (Linux/Mac)**
```bash
chmod +x swiftdeploy
```

**On Windows, run with Python:**
```bash
python swiftdeploy <subcommand>
```

## API Endpoints

The app runs on port 3000 internally and is accessible through Nginx on port 8080.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message with mode, version, and timestamp |
| GET | `/healthz` | Health check with uptime in seconds |
| POST | `/chaos` | Simulate degraded behaviour (canary mode only) |

### Chaos Endpoint Modes

```json
{ "mode": "slow", "duration": 3 }
```
Every request sleeps for 3 seconds before responding.

```json
{ "mode": "error", "rate": 0.5 }
```
50% of requests return a 500 error.

```json
{ "mode": "recover" }
```
Cancels all active chaos and returns to normal.

> The chaos endpoint is only available when running in canary mode.

## Subcommand Walkthrough

### `init`
Reads `manifest.yaml` and generates `nginx.conf` and `docker-compose.yml` from the templates. This is the foundation — everything else depends on these files.

```bash
python swiftdeploy init
```

---

### `validate`
Runs 5 checks before deploying to catch problems early. Exits with an error if any check fails.

```bash
python swiftdeploy validate
```

The 5 checks are:
1. `manifest.yaml` exists and is valid YAML
2. All required fields are present and not empty
3. The Docker image in the manifest exists locally
4. The Nginx port is not already in use
5. The generated `nginx.conf` has valid syntax

<img width="1716" height="583" alt="Screenshot 2026-05-03 235919" src="https://github.com/user-attachments/assets/a9ff0d09-1592-4f57-91e7-09b5f0778d9f" />


### `deploy`
Generates config files, starts all containers, and waits until the app passes its health check before returning. Times out after 60 seconds.

```bash
python swiftdeploy deploy
```

After deploy, access the app at `http://localhost:8080`

<img width="1560" height="422" alt="Screenshot 2026-05-04 002309" src="https://github.com/user-attachments/assets/f80d3c25-04ed-4bc3-a78d-31271150cd74" />


### `promote`
Switches the app between stable and canary mode without downtime. Only the app container restarts — Nginx keeps running throughout.

```bash
# Switch to canary mode
python swiftdeploy promote canary

# Switch back to stable
python swiftdeploy promote stable
```

What happens under the hood:
1. Updates `mode` in `manifest.yaml`
2. Regenerates `docker-compose.yml` with the new mode
3. Restarts only the app container
4. Hits `/healthz` to confirm the switch worked

<img width="955" height="703" alt="Screenshot 2026-05-04 002939" src="https://github.com/user-attachments/assets/ea4733f3-f580-491a-a00a-fd528ee9fa52" />


### `teardown`
Stops and removes all containers, networks, and volumes.

```bash
# Stop everything
python swiftdeploy teardown

# Stop everything and delete generated config files
python swiftdeploy teardown --clean
```

## Nginx Access Logs
Every request through Nginx is logged in this format:
timestamp | status | response_time | upstream_address | request

To View logs:
```bash
docker logs swiftdeploy-nginx
```
<img width="1077" height="878" alt="Screenshot 2026-05-04 003620" src="https://github.com/user-attachments/assets/366f47f3-83fb-46e1-81f8-5ab1d7ed338b" />


## Security

- App runs as a non-root user inside the container
- All Linux capabilities are dropped
- The app port is never exposed directly to the host — all traffic goes through Nginx
- Nginx config is mounted as read-only


## Nginx Access Logs

Every request through Nginx is logged in this format:
