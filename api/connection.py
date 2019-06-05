

class Connection:
    def __init__(self, db):
        self.db = db
        if hasattr(db, 'connection'):
            self.connection = db.connection()
        else:
            self.connection = db.get_con()

    def execute_procedure(self, procedure, params):
        try:
            cursor = self.connection.cursor()
            cursor.callproc(procedure, params)
            field_names = [d[0].lower() for d in cursor.description]
            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append(dict(zip(field_names, row)))

            if len(result) == 0:
                return [[]]
            return result
        except Exception as e:
            raise e
        finally:
            cursor.close()