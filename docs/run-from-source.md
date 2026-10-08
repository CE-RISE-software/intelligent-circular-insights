# Run from source

The workbench has a Python API and a browser interface. These instructions use
the source repository; they do not require a container image. Run the Python
commands from the repository root so the application can find its included data,
schemas and `.env` file.

## Local use

Install Python 3.10-3.12, [uv](https://docs.astral.sh/uv/) and Node.js 20 or newer.
From the repository root, install the dependencies:

```bash
make setup
make web
```

Start the API in one terminal:

```bash
make demo
```

Start the browser interface in another:

```bash
cd apps/web
npm run dev -- --port 5173
```

Open <http://localhost:5173>. The development server forwards `/api` requests
to the API at <http://127.0.0.1:8000>; check its status at
<http://127.0.0.1:8000/api/health>. `make demo` enables automatic reload and is
for local development, not a long-running installation.

The default `LLM_CASSETTE_MODE=replay` does not contact a model provider. Features
that need a model response may have no matching recorded response; validation and
other deterministic operations remain available. To use live model responses,
copy `.env.example` to `.env`, set `LLM_CASSETTE_MODE=live` and supply
`OPENAI_API_KEY`, then restart the API. Keep `.env` out of version control.

## Long-running installation

This example uses a Linux host with systemd and Nginx. Install Python 3.10-3.12,
uv, Node.js 20 or newer, and Nginx. Check out a chosen repository revision in a
stable location accessible to the service account. In the commands and examples
below, replace `/srv/intelligent-circular-insights` with that location and `ici`
with the service account.

As the service account, run from the repository root:

```bash
uv sync --locked --all-packages --no-dev
make web
cd apps/web
npm run build
```

The frontend build is in `apps/web/dist`. `make web` installs the frontend
dependencies outside the repository and links them into `apps/web/node_modules`.
Return to the repository root before starting the API. If live model responses
are needed, create `.env` there from `.env.example`, set
`LLM_CASSETTE_MODE=live` and `OPENAI_API_KEY`, and restrict the file to the
service account. Without these settings, the API stays in offline replay mode.

For example, install this systemd unit as
`/etc/systemd/system/intelligent-circular-insights.service`:

```ini
[Unit]
Description=Intelligent Circular Insights API
After=network.target

[Service]
Type=simple
User=ici
WorkingDirectory=/srv/intelligent-circular-insights
ExecStart=/srv/intelligent-circular-insights/.venv/bin/uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Start it and check the API:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now intelligent-circular-insights
curl http://127.0.0.1:8000/api/health
```

Serve the built frontend and forward `/api` to the API on the same host. An
Nginx server block can use the following locations (replace the host and root):

```nginx
server {
    listen 80;
    server_name insights.example.org;
    root /srv/intelligent-circular-insights/apps/web/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

The `/api/` prefix must be preserved when proxying. Configure HTTPS and an
appropriate access policy before accepting private records or exposing this
installation beyond a trusted network. After changing source, sync dependencies
again if the lockfile changed, rebuild the frontend if its source changed, and
restart the API. Check the public `/api/health` route and load the browser
interface after each update.
