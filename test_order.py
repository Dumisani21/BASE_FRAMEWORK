"""Simple test for order_by"""
from base import Model, CharField, IntegerField, Database

class TestModel(Model):
    id = IntegerField(primary_key=True, auto_increment=True)
    name = CharField(max_length=100)

# Setup
db = Database('test_order.db')
db.connect()
TestModel._create_table()

# Create some records
TestModel(name='Alice').save()
TestModel(name='Bob').save()
TestModel(name='Charlie').save()

# Test order_by
print("Testing order_by...")
try:
    results = TestModel.objects.order_by('name')
    print(f"Order by name: {[r.name for r in results]}")
    
    first = TestModel.objects.order_by('name').first()
    print(f"First: {first.name}")
    
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
