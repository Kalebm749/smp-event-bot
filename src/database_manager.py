import sqlite3
from datetime import datetime

class db_manager():

    def __init__(self, database, schema_file):
        self.db = database
        self.schema_file = schema_file


    # Connects to the database and returns a cursor object as well as the connection
    def db_connect(self):
        connection = sqlite3.connect(self.db)
        return connection


    # Grabs useful information about the database
    def db_info(self):
        db_conn = None

        try:
            with self.db_connect() as db_conn:
                cursor = db_conn.cursor()

                # Table Information
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in cursor.fetchall()]

                # Table row Information
                counts = {}

                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    counts[table] = cursor.fetchone()[0]

                return{
                    "tables": tables,
                    "row_counts": counts
                }

        except Exception as e:
            print(f"Error getting db_info. Exception: {e}")


    def initialize_db(self):
        db_conn = None

        try:
            with self.db_connect() as db_conn:

                with open(self.schema_file, "r") as f:
                    schema_sql = f.read()
                db_conn.executescript(schema_sql)
                db_conn.commit()
        except Exception as e:
            print(f"Error initalizing with Schema: {self.schema_file}. Exception {e}")


    def db_query(self, query):
        result = None
        db_conn = None

        try:
            with self.db_connect() as db_conn:
                cursor = db_conn.cursor()
                cursor.execute(query)
                result = cursor.fetchall()
                cursor.close()

        except Exception as e:
            print(f"Error querying the database: {e}")

        return result


    def db_backup(self, backup_dir) -> bool:

        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f'{backup_dir}{self.db.strip(".db")}_{backup_timestamp}'

        try:
            import shutil
            shutil.copy2(self.db, backup_path)
            print(f"Created backup file at {backup_path}")
            return True
        
        except Exception as e:
            print(f"Could backup database: {e}")
    
    def display_table(self, table):
        
        table_exists_query = f"""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name='{table}'
        """

        table_exists = ( len(self.db_query(table_exists_query)) > 0 )

        if table_exists:
            get_table_rows = self.db_query(f"SELECT * FROM {table};")
            return get_table_rows
        else:
            return None