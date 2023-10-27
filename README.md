# fatbot

## Install

You need mysqlclient installed. `sudo apt-get install libmysqlclient-dev` or `brew install mysql-client`
or whatever.

- `pip install virtualenv`
- `cd /path/to/project`  
- `virtualenv .venv --python=python3.10`
- `source .venv/bin/activate`
- `pip install pipenv`
- `pipenv install`
    "UserWarning: Unknown distribution option: 'descriptions'" when installing uwsgi?
    `LDFLAGS=-fno-lto pip install uwsgi`, then repeat
- `export TELEGRAM_TOKEN=...`
- `export OWNER_TELEGRAM_ID=...`
- `export DB_HOST=127.0.0.1`
- `export DB_NAME=fatbot`
- `export DB_USER=fatbot`
- `export DB_PASSWORD=fatbot`
- `alembic upgrade head`
- `python fatbot.py`

### docker?

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

- `pipenv install --dev`
- `alembic upgrade head`
- `pytest`
