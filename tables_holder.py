"""
Class for backup and restore customer tables from PostgreSQL database using SQLAlchemy engine

How to use:
backup = TablesHolder(engine=engine)
backup.backup()
backup.restore()
"""
from tempfile import NamedTemporaryFile


class TablesHolder(object):
    def __init__(self, engine):
        self.engine = engine
        self.files_path = {}
        self.connection = None
        self._table_list = []
        self.sequences = {}

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
            self.connection.execute(
                'ALTER TABLE {} DISABLE TRIGGER ALL'.format(table_name)
            )

    def _enable_triggers(self):
        for table_name in self.table_list:
            self.connection.execute(
                'ALTER TABLE {} ENABLE TRIGGER ALL'.format(table_name)
            )

    def _truncate_tables(self):
        for table_name in self.table_list:
            self.connection.execute(
                'TRUNCATE TABLE {0} CASCADE;'.format(table_name)
            )

    def _backup_tables(self):
        for table_name in self.table_list:
            self.files_path[table_name] = NamedTemporaryFile(mode='w+')
            self.connection.execute(
                "COPY {} TO '{}' WITH CSV;".format(
                    table_name, self.files_path[table_name].name
                )
            )

    def _backup_sequences(self):
        seq_sql = """
        SELECT sequence_schema || '.' || sequence_name
        FROM information_schema.sequences
        """
        for sequence_name in self.connection.execute(seq_sql):
            sequence_name = sequence_name[0]
            sql = "SELECT last_value FROM {}".format(sequence_name)
            value = self.connection.execute(sql).fetchone()
            self.sequences[sequence_name] = value[0]

    def _restore_tables(self):
        for table_name in self.table_list:
            self.connection.execute(
                "COPY {0} FROM '{1}' WITH CSV;".format(
                    table_name, self.files_path[table_name].name
                )
            )

    def _restore_sequences(self):
        for seq_name, seq_value in self.sequences.items():
            self.connection.execute(
                "SELECT setval('{}', {});".format(seq_name, seq_value)
            )

    def backup(self):
        self.connection = self.engine.connect()
        try:
            self._backup_sequences()
            self._backup_tables()
        finally:
            self.connection.close()

    def restore(self):
        self.connection = self.engine.connect()
        trans = self.connection.begin()
        try:
            self._disable_triggers()
            self._truncate_tables()
            self._restore_tables()
            self._restore_sequences()
            self._enable_triggers()
            trans.commit()
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            self.connection.close()
