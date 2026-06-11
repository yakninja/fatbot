# fatbot

## Install

You need Python 3.10 and mysqlclient build dependencies installed.

Ubuntu:

```
sudo apt-get install build-essential pkg-config default-libmysqlclient-dev
```

macOS:

```
brew install mysql-client pkg-config
export PATH="$(brew --prefix mysql-client)/bin:$PATH"
export PKG_CONFIG_PATH="$(brew --prefix mysql-client)/lib/pkgconfig"
```

- `cd /path/to/project`  
- `python3.10 -m venv .venv`
- `source .venv/bin/activate`
- `python -m pip install --upgrade pip`
- `python -m pip install -r requirements.txt`
- `export TELEGRAM_TOKEN=...`
- `export OWNER_TELEGRAM_ID=...`
- `export DB_HOST=127.0.0.1`
- `export DB_NAME=fatbot`
- `export DB_USER=fatbot`
- `export DB_PASSWORD=fatbot`
- `alembic upgrade head`
- `python fatbot.py`

### Docker

- `cp .env.example .env`
- `nano .env`
- `docker compose up --build app`

Useful database shell:

- `docker compose exec mysql mysql -uroot -proot`
- `CREATE USER 'fatbot'@'192.168.%' IDENTIFIED BY 'fatbot';`
- `GRANT ALL ON fatbot.* to fatbot@'192.168.%';`

## Alembic cheatsheet

### Create revision

```
alembic revision -m "revisionname"
```

### Bring database to the latest revision

```
alembic upgrade head
```

### Rollback the latest revision

```
alembic downgrade -1
```

### Testing

- `python3.10 -m venv .venv`
- `source .venv/bin/activate`
- `python -m pip install --upgrade pip`
- `python -m pip install -r requirements-dev.txt`
- `alembic upgrade head`
- `pytest`


### Service

- `cp .env.example .env`
- `nano .env`
- `sudo cp fatbot.service.example /etc/systemd/system/fatbot.service`
- `sudo nano /etc/systemd/system/fatbot.service`
- `sudo systemctl daemon-reload`
- `sudo systemctl start fatbot`
- `sudo systemctl enable fatbot`
- `sudo visudo`
- add `yakninja ALL=(ALL:ALL) NOPASSWD: /bin/systemctl start fatbot, /bin/systemctl stop fatbot, /bin/systemctl restart fatbot`
- see logs with `journalctl -f -u fatbot`
