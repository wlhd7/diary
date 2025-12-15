# Deploy examples

This folder contains example systemd and Nginx configuration snippets you can adapt for production.

Files
- `diary.service` — systemd unit that runs Gunicorn from `/opt/diary/.venv` and the application at `/opt/diary/current`.
- `nginx.conf` — Nginx site config that serves static files from `/opt/diary/current/static` and proxies requests to `127.0.0.1:8000`.

Quick install steps (example):

1. Copy application artifacts to `/opt/diary/current` and install a venv at `/opt/diary/.venv`.

2. Place the systemd unit and enable it:
```
sudo cp deploy/diary.service /etc/systemd/system/diary.service
sudo systemctl daemon-reload
sudo systemctl enable --now diary.service
sudo journalctl -u diary -f
```

3. Install Nginx site and reload:
```
sudo cp deploy/nginx.conf /etc/nginx/sites-available/diary
sudo ln -s /etc/nginx/sites-available/diary /etc/nginx/sites-enabled/diary
sudo nginx -t && sudo systemctl reload nginx
```

4. Put runtime secrets in `/etc/default/diary` or use your secret manager and ensure the service user has access.

Notes
- Adjust `User`, paths, and domain names to your environment. Do not run services as root.
- Use HTTPS in production; obtain certs with Certbot or a managed provider.
- These are examples — validate and harden them before using in production.
