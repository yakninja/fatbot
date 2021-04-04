import os


def get_db_url():
    return "mysql://%s:%s@%s/%s" % (
        os.getenv("DB_USER", "fatbot"),
        os.getenv("DB_PASSWORD", "fatbot"),
        os.getenv("DB_HOST", "localhost"),
        os.getenv("DB_NAME", "fatbot"),
    )