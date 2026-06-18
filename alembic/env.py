import os
import re
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text

from alembic import context
from cnaas_nac.core.settings import settings
from cnaas_nac.models.base import Base

sys.path.append("src")


def get_next_prefix(versions_dir: str) -> str:
    """Scan existing migration files and return the next numeric prefix."""
    if not os.path.isdir(versions_dir):
        return "01"

    max_num = 0
    pattern = re.compile(r"^(\d+)_")

    for filename in os.listdir(versions_dir):
        match = pattern.match(filename)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num

    return f"{max_num + 1:02d}"


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

config.set_main_option(
    "sqlalchemy.url",
    f"{settings.POSTGRES_SYNC_PREFIX}{settings.POSTGRES_URI}",
)

# Get the versions directory from alembic config
versions_dir = config.get_main_option("version_locations", "alembic/versions")

# Inject the custom file template with the next prefix
next_prefix = get_next_prefix(versions_dir)
config.set_main_option("file_template", f"{next_prefix}_%%(rev)s_%%(slug)s")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from cnaas_nac.models.endpoint import *  # noqa: E402, F403
from cnaas_nac.models.nas import *  # noqa: E402, F403
from cnaas_nac.models.nas_port import *  # noqa: E402, F403
from cnaas_nac.models.policy import *  # noqa: E402, F403
from cnaas_nac.models.radacct import *  # noqa: E402, F403
from cnaas_nac.models.radpostauth import *  # noqa: E402, F403
from cnaas_nac.models.rbac import *  # noqa: E402, F403

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an Engine is acceptable here as well.  By
    skipping the Engine creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="alembic_schema",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Create the schema for the Alembic version table if it doesn't exist
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS alembic_schema;"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="alembic_schema",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
