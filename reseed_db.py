import os

# Delete old database to re-seed
if os.path.exists('swasthya_sarthi.db'):
    os.remove('swasthya_sarthi.db')
    print('Old database deleted')

# Import and run seed
from backend.seed_loader import seed_data
seed_data()
