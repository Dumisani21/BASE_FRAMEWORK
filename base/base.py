import sqlite3

class Database:

	def __init__(self, db_name):
		try:
			self.conn = sqlite3.connect(db_name)
			self.c = self.conn.cursor()
			print(f"Connected to database '{db_name}'")
		except sqlite3.Error as e:
			print(f"Error connecting to database: {e}")

	def __del__(self):
		self.conn.close()

	def create_table(self, table_name, attributes):
		try:
			self.c.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({attributes})")
			print(f"Table '{table_name}' created successfully")
		except sqlite3.Error as e:
			print(f"Error creating table: {e}")

	def insert_data(self, table_name, data):
		try:
			placeholder = '?'
			placeholders = ', '.join(placeholder * len(data))
			self.c.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", data)
			self.conn.commit()
			print(f"{self.c.rowcount} rows inserted successfully")
		except sqlite3.Error as e:
			print(f"Error inserting data: {e}")

	def update_data(self, table_name, set_clause, where_clause):
		try:
			self.c.execute(f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}")
			self.conn.commit()
			print(f"{self.c.rowcount} rows updated successfully")
		except sqlite3.Error as e:
			print(f"Error updating data: {e}")

	def delete_data(self, table_name, where_clause):
		try:
			self.c.execute(f"DELETE FROM {table_name} WHERE {where_clause}")
			self.conn.commit()
			print(f"{self.c.rowcount} rows deleted successfully")
		except sqlite3.Error as e:
			print(f"Error deleting data: {e}")

	def drop_table(self, table_name):
		try:
			self.c.execute(f"DROP TABLE IF EXISTS {table_name}")
			self.conn.commit()
			print(f"Table '{table_name}' dropped successfully")
		except sqlite3.Error as e:
			print(f"Error dropping table: {e}")

	def view_data(self, table_name, columns='*', where_clause=None):
		try:
			if where_clause:
				self.c.execute(f"SELECT {columns} FROM {table_name} WHERE {where_clause}")
			else:
				self.c.execute(f"SELECT {columns} FROM {table_name}")
			data = self.c.fetchall()
			print(f"{len(data)} rows returned")
			return data
		except sqlite3.Error as e:
			print(f"Error viewing data: {e}")