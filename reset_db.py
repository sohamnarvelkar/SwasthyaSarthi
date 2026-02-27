from backend.database import Base, engine
from backend.models import Order, Medicine, Patient
from sqlalchemy import inspect

print('Dropping all tables...')
Base.metadata.drop_all(bind=engine)
print('Creating all tables with new schema...')
Base.metadata.create_all(bind=engine)
print('Database recreated successfully!')
print('Order table columns:')
inspector = inspect(engine)
columns = inspector.get_columns('orders')
for col in columns:
    print(f'  - {col["name"]}: {col["type"]}')
