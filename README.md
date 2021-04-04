# fatbot

## Install

- `pip install virtualenv`
- `cd /path/to/project`  
- `virtualenv venv`
- `source venv/bin/activate`
- `pip install -r requirements.txt`
- `export TELEGRAM_TOKEN=...`
- `export OWNER_USER_ID=...`
- `export DB_HOST=127.0.0.1`
- `export DB_NAME=fatbot`
- `export DB_USER=fatbot`
- `export DB_PASSWORD=fatbot`
- `alembic upgrade head`
- `python fatbot.py`

### docker?

- `docker-compose exec mysql mysql -uroot -proot`
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