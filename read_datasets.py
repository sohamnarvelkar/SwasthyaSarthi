import pandas as pd

# Read products-export.xlsx
print('=== PRODUCTS EXPORT ===')
df = pd.read_excel('data/products-export.xlsx')
print('Columns:', list(df.columns))
print('Shape:', df.shape)
print()
print(df.head(10).to_string())
print()

print('=== CONSUMER ORDER HISTORY ===')
df2 = pd.read_excel('data/Consumer Order History 1.xlsx')
print('Columns:', list(df2.columns))
print('Shape:', df2.shape)
print()
print(df2.head(10).to_string())
