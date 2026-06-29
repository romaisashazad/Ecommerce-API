from shop.db import products_collection

print("Connected! Current documents in products collection:")
print(list(products_collection.find()))