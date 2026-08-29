# NetHack

NetHack is an authorized network diagnostics dashboard for Windows, macOS, Linux, Ubuntu, and Android (Termux), with an iOS browser-only mode.

## Security model

- Only allowlisted, read-only diagnostics are executable.
- No credential extraction, Wi-Fi password disclosure, persistence, privilege escalation, exploitation, or arbitrary shell execution.
- Target probing is limited to a user-specified host and optional single TCP port.
- Use this project only on systems and networks you own or administer.

## Stack

- Django 5.x
- Tkinter desktop collector
- HTMX
- Alpine.js
- Tailwind CSS CDN
- hyperscript CDN
- Motion One CDN
- sql.js CDN
- Vercel Python runtime

## Architecture

`browser -> Django on Vercel` for UI/API, while `browser -> 127.0.0.1:8765` can reach the local diagnostic agent when installed on the endpoint. Vercel itself cannot execute commands on a visitor's PC or phone.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

### Local diagnostic agent

```bash
python collector/agent.py
```

The agent listens only on `127.0.0.1:8765`.

### Tkinter

```bash
python desktop/tk_app.py
```

## Vercel

Vercel can serve Django through its Python runtime/WSGI entry point. Set `DJANGO_SECRET_KEY` in project settings/environment variables. The included `vercel.json` routes application requests to `nethack/wsgi.py` and uses Django's normal static/template setup.

```bash
vercel
```

## Features

- Local interface, IP, MAC, gateway, routes, ARP/neighbor cache, DNS, sockets, listening ports, firewall status where available
- Ping, reverse DNS, single-port TCP connect, and route/traceroute to a specified target
- Normalized report view
- UTF-8 CSV export
- UTF-8 SQL export generated in-browser from sql.js
- Raw command-output preservation for auditability

## Platform limitations

- iOS Safari/WebKit does not provide a supported way for a normal web page to run arbitrary shell commands. NetHack therefore exposes browser-visible diagnostics only and provides manual commands for iOS.
- Linux `netstat` may not be installed; `ss` is preferred.
- Android command availability depends on Termux/device permissions.
