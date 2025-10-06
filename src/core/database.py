"""Database connection management via SQLAlchemy engine with psycopg DSN construction."""

import logging
import os
from time import sleep

from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.exc import OperationalError, StatementError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.query import Query as _Query
from . import config

if config.DEPLOYMENT != "PRODUCTION":
    load_dotenv(override=False)

logger = logging.getLogger(__name__)


def _dsn_from_env() -> str:
    """Construct a SQLAlchemy DSN using env vars."""
    db_type = config.DBTYPE
    driver = config.DB_DRIVER
    user = config.DB_USERNAME
    password = config.DB_PASSWORD
    host = config.DB_HOST
    port = config.DB_PORT
    name = config.DB_NAME

    sslmode = config.DB_SSLMODE or config.DB_LOCAL_SSLMODE
    if sslmode:
        return f"{db_type}+{driver}://{user}:{password}@{host}:{port}/{name}?sslmode={sslmode}"
    return f"{db_type}+{driver}://{user}:{password}@{host}:{port}/{name}"


SQLALCHEMY_DATABASE_URL = _dsn_from_env()
logger.info("SQLALCHEMY_DATABASE_URL: %s", SQLALCHEMY_DATABASE_URL)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=config.DB_POOL_RECYCLE,
    pool_timeout=config.DB_POOL_TIMEOUT,
    pool_size=config.DB_POOL_MIN,
    max_overflow=config.DB_POOL_MAX,
)


def init_db_pool() -> None:
    """Eagerly validate that the SQLAlchemy engine can obtain a connection."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        logger.exception("[DB] Failed to initialise SQLAlchemy engine")
        raise


class RetryingQuery(_Query):
    __max_retry_count__ = config.DB_MAX_RETRIES

    def __iter__(self):
        attempts = 0
        max_attempts = self.__max_retry_count__
        while True:
            attempts += 1
            try:
                return super().__iter__()
            except OperationalError as ex:
                if "server closed the connection unexpectedly" not in str(ex):
                    raise
                if attempts <= max_attempts:
                    sleep_for = 2 ** (attempts - 1)
                    logger.error(
                        "Database connection error: retrying Strategy => sleeping for %ss and will retry (attempt #%s of %s )\nDetailed query impacted: %s",
                        sleep_for,
                        attempts,
                        max_attempts,
                        ex,
                    )
                    sleep(sleep_for)
                    continue
                raise
            except StatementError as ex:
                message = "reconnect until invalid transaction is rolled back"
                if message not in str(ex):
                    raise
                self.session.rollback()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
    query_cls=RetryingQuery,
)

metadata = MetaData()
Base = declarative_base(metadata=metadata)