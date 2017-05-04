"""
Class for backup and restore customer tables from PostgreSQL database using SQLAlchemy engine
"""


class TablesHolder(object):
    def __init__(self, engine, backup_dir):
        self.engine = engine
        self.backup_dir = backup_dir
        self._table_list = []

    @property
    def table_list(self):
        if not self._table_list:
            sql = """
                SELECT schemaname, tablename FROM pg_catalog.pg_tables
                WHERE schemaname != 'pg_catalog'
                AND schemaname != 'information_schema';
            """
            self._table_list = [
                '{}.{}'.format(row.schemaname, row.tablename)
                for row in self.engine.execute(sql)
            ]
        return self._table_list

    def _disable_triggers(self):
        for table_name in self.table_list:
            self.engine.execute(
                'ALTER TABLE {} DISABLE TRIGGER ALL'.format(table_name)
            )

    def _enable_triggers(self):
        for table_name in self.table_list:
            self.engine.execute(
                'ALTER TABLE {} ENABLE TRIGGER ALL'.format(table_name)
            )

    def _backup_table(self, table_name):
        file_name = os.path.join(
            self.backup_dir, '{}.csv'.format(table_name)
        )
        self.engine.execute(
            "COPY {} TO '{}' WITH CSV;".format(table_name, file_name)
        )

    def _restore_table(self, table_name):
        file_name = os.path.join(
            self.backup_dir, '{}.csv'.format(table_name)
        )
        self.engine.execute(
            """
            BEGIN;
                TRUNCATE TABLE {0} CASCADE ;
                COPY {0} FROM '{1}' WITH CSV;
            COMMIT;
            """.format(table_name,file_name)
        )

    def backup(self):
        for table_name in self.table_list:
            self._backup_table(table_name)

    def restore(self):
        self._disable_triggers()
        for table_name in self.table_list:
            self._restore_table(table_name)
        self._enable_triggers()


backup = TablesHolder(engine=engine, backup_dir='/path/to/dir')
backup.backup()
backup.restore()
