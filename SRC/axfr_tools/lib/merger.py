import sqlite3 as lite

class Merger():
    """Handles merging two SQLite databases into a new one."""
    
    def get_table_names(self, conn):
        """Retrieve all table names from a database."""
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        return [table[0] for table in tables]


    def get_full_table_schema(self, conn, table_name):
        """Retrieve the full schema (CREATE TABLE statement) for a specific table."""
        cursor = conn.cursor()
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        schema = cursor.fetchone()
        if schema:
            return schema[0]
        else:
            return None


    def merge_databases(self, db1_path, db2_path, new_db_path):
        """Merge two databases into a new database."""
        try:
            with lite.connect(db1_path, timeout=30) as conn1, \
                 lite.connect(db2_path, timeout=30) as conn2, \
                 lite.connect(new_db_path, timeout=30) as new_db_conn:
                
                ## Env setup
                new_db_conn.execute("PRAGMA journal_mode=WAL;")
                new_db_conn.execute("PRAGMA synchronous=NORMAL;")
                new_db_conn.execute(f"ATTACH DATABASE '{db1_path}' AS db1;")
                new_db_conn.execute(f"ATTACH DATABASE '{db2_path}' AS db2;")
                
                ## Table info
                tables_db1 = self.get_table_names(conn1)
                tables_db2 = self.get_table_names(conn2)
                
                ## db1
                for table in tables_db1:
                    create_table_sql = self.get_full_table_schema(conn1, table)
                    if create_table_sql:
                        new_db_conn.execute(create_table_sql)
                        cursor1 = conn1.cursor()
                        cursor1.execute(f"SELECT * FROM {table}")
                        rows = cursor1.fetchall()
                        for row in rows:
                            try:
                                placeholders = ', '.join(['?' for _ in row])
                                new_db_conn.execute(f"INSERT INTO {table} VALUES ({placeholders})", row)
                            except lite.IntegrityError as e:
                                pass
                            except Exception as e:
                                print(f"[!] Unexpected error while inserting row into {table} from {db1_path}: {e}")
                
                ## db2
                for table in tables_db2:
                    if table in tables_db1:
                        create_table_sql_db2 = self.get_full_table_schema(conn2, table)
                        create_table_sql_db1 = self.get_full_table_schema(conn1, table)
                        
                        ## schema checks
                        if create_table_sql_db1 == create_table_sql_db2:
                            cursor2 = conn2.cursor()
                            cursor2.execute(f"SELECT * FROM {table}")
                            rows = cursor2.fetchall()
                            for row in rows:
                                try:
                                    placeholders = ', '.join(['?' for _ in row])
                                    new_db_conn.execute(f"INSERT INTO {table} VALUES ({placeholders})", row)
                                except lite.IntegrityError as e:
                                    pass
                                except Exception as e:
                                    print(f"[!] Unexpected error while inserting row into {table} from {db2_path}: {e}")
                        else:
                            print(f"[!] Schema mismatch for table {table} between {db1_path} and {db2_path}. Skipping.")
                    else:
                        print(f"[!] Table {table} from {db2_path} does not exist in {db1_path}, skipping.")
                
                ## Cleanup
                new_db_conn.commit()
                new_db_conn.execute("DETACH DATABASE db1;")
                new_db_conn.execute("DETACH DATABASE db2;")
        
        except lite.Error as e:
            print(f"SQLite error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
