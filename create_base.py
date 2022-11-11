'''
BASE v1.0.0
Base is a no-sql database created with python3
'''
import sqlite3
import sys, os

class BASE:

    def __init__(self, file_path, db_name):

        self.file_path = file_path
        self.db_name = db_name


    def db_connect(self):
        conn = ''
        if not self.file_path == '':
            conn = sqlite3.connect(f'{self.file_path}/{self.db_name}')
        else:
            conn = sqlite3.connect(self.db_name)

        return conn
    
    
    


    def create_db_cols(self,table_name, cols_names={}):

        build_cols = ''
        
        print(cols_names)
        
        count = 0
        length = len(cols_names)
        for col_name, col_type in cols_names.items():
            count += 1
            if not count == length:
                build_cols += f'{col_name} {col_type}, '
            else:
                build_cols += f'{col_name} {col_type} '
            
        build_cols = build_cols.strip()
        
        conn = self.db_connect()
        cursor = conn.cursor()
        query = f"CREATE TABLE {table_name} ({build_cols})"
        cursor.execute(query)
        conn.commit()
        conn.close()
        
        return 'Tables where created'
        

    def insert_rows(self,table_name, rows={}):
        
        conn = self.db_connect()
        cursor = conn.cursor()
        placeholder = ','.join('?' for _ in range(len(rows)))
    
        build_value = ''
        
        count = 0
        for col_name, value in rows.items():
            count += 1
            if not count == len(rows):
                build_value += f'{value},'
            else:
                build_value += f'{value}'
                
        query = (f"INSERT INTO {table_name} VALUES ({placeholder})",(build_value))
        cursor.execute(query)
        conn.commit()
        conn.close()
                
    

    def remove_rows(self, rows={}):
        
        pass

    def read_rows(self, rows={}):

        pass

    def read_all_rows(self):

        pass
