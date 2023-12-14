import psycopg2
from psycopg2 import sql
from datetime import datetime
class PostgresLoggingEngine:
    def __init__(self, connection_string):
        self.connection = psycopg2.connect(connection_string)
        self.cursor = connection.cursor()
        self.generic_log_insertion="INSERT INTO {} (_dtu, Ancestor, Current, Descendant, {}) VALUES ({}, {}, {}, {}, {})"
        for filename in os.listdir("migrations"):
            if filename.endswith('.sql') and os.path.isfile(file_path):
                sql=open(file_path)
                self.cursor.execute(sql.read())
                sql.close()

    def logs_request(obj):
        try:
            self.cursor.execute(sql.SQL(generic_log_insertion).format(
                "trace_request",
                "request",
                datetime.now(),
                obj.headers["X-Ancestor"],
                obj.headers["X-Current"],
                obj.headers["X-Descendant"],
                str(obj)
            ))
            self.cursor.commit()
        except:
            print("InsertRequestError")
            return False
        return True

    def logs_response(obj):
        try:
            self.cursor.execute(sql.SQL(generic_log_insertion).format(
                "trace_response",
                "response",
                datetime.now(),
                obj.headers["X-Ancestor"],
                obj.headers["X-Current"],
                obj.headers["X-Descendant"],
                str(obj)
            ))
            self.cursor.commit()
        except:
            print("InsertResponseError")
            return False
        return True