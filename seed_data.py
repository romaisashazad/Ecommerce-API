from shop.db import products_collection

products_collection.delete_many({})

sample_products = [
    {
        "name": "Men's Classic Shirt",
        "price": 2500,
        "category": "Men",
        "description": "A classic cotton shirt for formal and casual wear.",
        "is_deleted": False
    },
    {
        "name": "Women's Embroidered Kurta",
        "price": 4200,
        "category": "Women",
        "description": "Hand embroidered kurta in premium lawn fabric.",
        "is_deleted": False
    },
    {
        "name": "Unisex Sneakers",
        "price": 6800,
        "category": "Footwear",
        "description": "Comfortable everyday sneakers, breathable fabric.",
        "is_deleted": False
    },
    {
        "name": "Leather Handbag",
        "price": 5400,
        "category": "Accessories",
        "description": "Genuine leather handbag with adjustable strap.",
        "is_deleted": False
    }
]

result = products_collection.insert_many(sample_products)
print("Inserted IDs:", result.inserted_ids)