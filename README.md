# Base v2.0.0

### I made this program to help make sqlite3 less conplicated to use

## How to download Base.

### Just download the zip git repository or clone it on your system:
```bash
$git clone "paste clone link here without qoutes"
```
---

# How to use sqlite3 term

## 1. first import the package
```python
from base import base
```

## 2. Create database file and connect it
```python
# db = DATABASE('Name_DataBase.db')
db = base.Database('people.db')
```

## 3. Create Table
```python
# db.create_table('Table_Name',"(column_1 DataType, column_2 DataType,...)")
db.create_table('workers','firstName text,lastName text')
```

## 4. Insert data
```python
# insert_data( Name_of_Table, (John, Smith) ) 
# Remeber to put your data inside a tuple
db.insert_data('workers',('John','Smith'))
```

## 5. Update data
```python
#update_data('Table_Name',"column_1 = value_1, column_2 = value_2,...", where_clause)
db.update_data('workers',  "firstName = 'John', lastName = 'Goodman'",  "rowid = 1")
```

## 6. Delete data
```python
#delete_data('Table_Name','where_clause')
db.delete_data('workers','rowid = 1')
```

## 7. Drop Table
```python
# db.drop_table('Table_Name')
db.drop_table('workers')
```

## 8. View data all from table
```python
# db.view_data(table_name, columns='*', where_clause=None)

db.view_data('workers','rowid, firstName, lastName')
db.view_data('workers',  where_clause = "rowid = 1")
db.view_data('workers','firstName',  where_clause= "lastName = 'Smith'")
```