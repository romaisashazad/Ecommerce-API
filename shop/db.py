import os
from dotenv import load_dotenv
from pymongo import MongoClient        # opens a connection to MongoDB

load_dotenv()   # runs and reads dotenv files so mongo_uri is accessible

MONGO_URI = os.getenv("MONGO_URI")   # fetches what we wrote in .env file

client = MongoClient(MONGO_URI)   # opens the connection to atlas cluster using this string



db = client ["ecommerce_db"]        # for mongodb, no need to create  a db in advance, just point to it "ecomm.." here
products_collection = db["products"]   # collection -> same idea as table in SQL