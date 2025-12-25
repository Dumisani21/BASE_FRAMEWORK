"""Quick test to debug the datetime issue"""
from base import Model, CharField, IntegerField, DateTimeField, Database

class TestModel(Model):
    id = IntegerField(primary_key=True, auto_increment=True)
    name = CharField(max_length=100)
    created_at = DateTimeField(auto_now_add=True)

# Setup
db = Database('test_debug.db')
db.connect()
TestModel._create_table()

# Create instance
test = TestModel(name='Test')
print(f"Before save - created_at type: {type(test.created_at)}")
print(f"Before save - created_at value: {test.created_at}")

# Check field
field = TestModel._fields['created_at']
print(f"Field to_db result: {field.to_db(test.created_at)}")

# Try to save
try:
    test.save()
    print("Save successful!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
