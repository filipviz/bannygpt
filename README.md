Use Python 3.11.

```bash
virtualenv -p python3.11 venv
source venv/bin/activate
source .env
pip install -r requirements.txt

python setup-db.py

gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 main:app
```

If using with nginx, you may need to bind to a unix socket (`--bind unix:bannygpt.sock -m 007`) when using gunicorn.

## systemd config

```toml
[Unit]
Description=Gunicorn instance to serve BannyGPT
After=network.target

[Service]
User=root
Group=nginx
WorkingDirectory=/root/bannygpt
Environment="PATH=/root/bannygpt/venv/bin"
EnvironmentFile=-/root/bannygpt/.env
ExecStart=/root/bannygpt/venv/bin/gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 1 main:app

[Install]
WantedBy=multi-user.target
```

## nginx config

```
server {
    listen 80;
    server_name banny.club www.banny.club;

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_pass http://127.0.0.1:8000;
    }

    location /socket.io {
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_pass http://127.0.0.1:8000/socket.io;
    }
```

Upgrade with `certbot --nginx`
