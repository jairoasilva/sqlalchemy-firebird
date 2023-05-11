from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateTable, DropTable, CreateIndex, DropIndex
from sqlalchemy.testing.provision import temp_table_keyword_args

import logging


@temp_table_keyword_args.for_db("firebird")
def _firebird_temp_table_keyword_args(cfg, eng):
    return {
        "prefixes": ["GLOBAL TEMPORARY"],
        "firebird.fdb_on_commit": "PRESERVE ROWS",
        "firebird.firebird_on_commit": "PRESERVE ROWS",
    }


HAS_DDL_PENDING = False


@event.listens_for(Engine, "before_execute")
def receive_before_execute(connection, statement, *arg):
    #
    # Important: Statements executed with connection.exec_driver_sql() don't pass through here.
    #            Use connection.execute(text()) instead.
    # 
    global HAS_DDL_PENDING

    if isinstance(statement, (CreateTable, DropTable, CreateIndex, DropIndex)):
        HAS_DDL_PENDING = True
        return

    if HAS_DDL_PENDING:
        log = logging.getLogger("sqlalchemy.firebird.provision")
        log.warning("Flushing DDL, conn = %s", str(connection))

        # Using Connection protected methods here because the public ones cause errors with TransactionManager
        connection._commit_impl()
        connection._begin_impl(connection._transaction)

        HAS_DDL_PENDING = False
