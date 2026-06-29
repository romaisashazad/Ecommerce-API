import json   # for reading the request
from django.views.decorators.csrf import csrf_exempt # bec django blcoks post, put, delete from other origins by default for security
from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse      # django tool for sending back json
from .db import products_collection    # . -> from the same folder as this file, geting prod_coll from shop

from bson import ObjectId
from bson.errors import InvalidId

def serialize_product(product):       # takes the dictionary called product, converts its id to string
    product["_id"] = str(product["_id"])   
    return product                      # returns dictionary 


def serialize_products(products):   # returning list of products
    ser_list = []
    for product in products:
        ser_item = serialize_product(product)
        ser_list.append(ser_item)
    return ser_list

def exclude_deleted(query_filter):         # modfies a filter dict before it gets sent to db
    query_filter["is_deleted"] = False      # gets only active products
    return query_filter

def validate_product_data(data, require_all=True):
    # 1. Check name
    if require_all or "name" in data:
        name = data.get("name")
        if not name or type(name) is not str or len(name) > 100:
            return "Invalid product name"
        if not any(char.isalpha() for char in name):     # reject names with no letters at all
            return "Product name must contain letters"
        
    # 2. Check price
    if require_all or "price" in data:
        price = data.get("price")
        if type(price) not in (float, int) or price <= 0:
            return "Invalid product price"

    # 3. check category
    if require_all or "category" in data:
        category = data.get("category", "")
        if type(category) is not str or len(category) > 50:
            return "Invalid product category"

    # 4. Check description
    if require_all or "description" in data:
        description = data.get("description", "")
        if type(description) is not str or len(description) > 500:
            return "Invalid product description"

    return None  # when everything is correct

@csrf_exempt
def create_product(request):
    try:
        data = json.loads(request.body)          # the new product comes in the request body as JSON, not URL. we trun raw json into python dict
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status = 400)
    
    error = validate_product_data(data) # require_all defaults to True

    if error is not None:
        return JsonResponse({"error": error}, status=400)

    new_product = {
        "name" : data.get("name"),
        "price" : data.get("price"),
        "category": data.get("category", ""),
        "description": data.get("description", ""),
        "is_deleted": False,
    }
    result = products_collection.insert_one(new_product)
    new_product["_id"] = result.inserted_id

    return JsonResponse(serialize_product(new_product), status = 201)

def list_products(request):
    query = {}
    # 1. filter by category
    category = request.GET.get("category")
    if category:
        query["category"] = category

    # 2. search by name
    search = request.GET.get("search")
    if search:
        query["name"] = {"$regex":search, "$options" : "i" }  # flexible text search smiliar to contains in sql, i = ignore upper/lowercase

    # 3.  Price filters
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    price_filter = {}
    if min_price:
        try:
            price_filter["$gte"] = float(min_price)
        except ValueError:
            return JsonResponse({"error": "min_price must be a number"}, status=400)

    if max_price:
        try:
            price_filter["$lte"] = float(max_price)
        except ValueError:
            return JsonResponse({"error": "max_price must be a number"}, status=400)

    if price_filter:
        query["price"] = price_filter
    # SOFT_DELETE
    query = exclude_deleted(query)

    
    # Start the cursor with whatever filter we built, pending req. find returns cursor object ->reps connection to db
    cursor = products_collection.find(query)

   # 4. Sorting
    sort_field = request.GET.get("sort")
    if sort_field:
        order = request.GET.get("order","asc")
        if order == "desc":
            direction = -1
        else:
            direction = 1
        cursor = cursor.sort(sort_field, direction) # reassign cursor to new sorted version

   # 5. Pagination
     #    ?limit=2&skip=0      first skip past, then apply next
    limit = request.GET.get("limit")
    skip = request.GET.get("skip")

    if skip:
        try:
            cursor = cursor.skip(int(skip))  # individual items inside cursor are dictionaries
        except ValueError:
            return JsonResponse({"error": "skip must be a number"}, status=400)

    if limit:
        try:
            cursor = cursor.limit(int(limit))
        except ValueError:
            return JsonResponse({"error": "limit must be a number"}, status=400)

    raw_products = list(cursor)  # applies every filter/sort/limit
    serialized_products = serialize_products(raw_products)
    
    #Return response back 
    return JsonResponse({
        "count": len(serialized_products), 
        "products": serialized_products
    })

def retrieve_product(request, product_id):  # single product get
    try:
        object_id = ObjectId(product_id)
    except InvalidId:
        return JsonResponse({"error": "Invalid product ID"}, status=400)
    
    # 1. building query dict
    query = {}
    query["_id"] = object_id  # using mongodb objid variable

    query = exclude_deleted(query)  # to get only active items
    product = products_collection.find_one(query)

    if product is None:
        return JsonResponse({"error": "Product not found"}, status=404)
    
    serialized_product = serialize_product(product)
    return JsonResponse(serialized_product)


def retrieve_product_by_query(request):
    product_id = request.GET.get("product_id") # looks for a key named product_id
 
    if not product_id:
        return JsonResponse({"error": "product_id query parameter is required"}, status= 400)
    try:
        object_id = ObjectId(product_id)
    except (InvalidId): 
        return JsonResponse({"error": "Invalid product ID"}, status= 400)
    
    query = {}
    query["_id"] = object_id  # using mongodb objid variable

    query = exclude_deleted(query)  # to get only active items
    product = products_collection.find_one(query)

    if product is None:
        return JsonResponse({"error": "Product not found"}, status= 404)

    serialized_product = serialize_product(product)
    return JsonResponse(serialized_product)


def update_product(request,product_id):
    #  ONLY allow PUT or PATCH for updating
    if request.method not in ("PUT","PATCH"):
        return JsonResponse({"error":"Method not allowed"}, status=405)
    
    # 1. Parse json payload
    try:
        data = json.loads(request.body)  # translating raw string to native python dict
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    # 2. Validate incoming ID
    try:
        object_id=ObjectId(product_id)
    except InvalidId:           
        return JsonResponse({"error": "Invalid product ID format"}, status=400)
    
    query = {"_id": object_id, "is_deleted": False}
    if request.method == "PUT":
        # PUT = full replacement, every field is required, the whole document is swapped
        error_message = validate_product_data(data, require_all=True)
        if error_message is not None:
            return JsonResponse({"error": error_message}, status=400)

        replacement = {
            "name": data["name"],
            "price": data["price"],
            "category": data.get("category", ""),
            "description": data.get("description", ""),
            "is_deleted": False,   # replace_one wipes EVERYTHING not listed, so we carry this flag forward
        }
        result = products_collection.replace_one(query, replacement)

    else:  # PATCH = partial update: only the fields we sent
        error_message = validate_product_data(data, require_all=False)
        if error_message is not None:
            return JsonResponse({"error": error_message}, status=400)

        allowed_fields = ["name", "price", "category", "description"]
        fields_to_update = {}
        for field in allowed_fields:
            if field in data:                 # key being PRESENT is the signal to update it
                fields_to_update[field] = data[field]

        if not fields_to_update:
            return JsonResponse({"error": "No valid fields to update"}, status=400)

        result = products_collection.update_one(query, {"$set": fields_to_update})

    if result.matched_count == 0:
        return JsonResponse({"error": "Product not found or inactive"}, status=404)

    updated_document = products_collection.find_one({"_id": object_id})
    serialized_product = serialize_product(updated_document)
    return JsonResponse({
        "success": True,
        "message": "Product updated successfully",
        "product": serialized_product,
    })
def delete_product(request,product_id):
    try:
        object_id=ObjectId(product_id)
    except InvalidId:           #catches any error
        return JsonResponse({"error": "Invalid product ID format"}, status=400)
    
    # Performing soft delete
    filter_query = {}
    filter_query["_id"] = object_id
    filter_query["is_deleted"] = False

    update_instruction = {"$set": {"is_deleted": True}}

    result = products_collection.update_one(filter_query,update_instruction)
    
    if result.matched_count == 0:                     # nothing matched -> it didn't exist, found id and active
        return JsonResponse({"error": "Product not found"}, status=404)
    return JsonResponse({"message": "Product deleted"})


@csrf_exempt
def product_detail_router(request,product_id):
    # look at built-in HTTP verb (GET, PUT, PATCH,DELETE)
    method = request.method

    if method =="GET":
        return retrieve_product(request,product_id)
    elif method in ("PUT","PATCH"):
        return update_product(request,product_id)
    elif method == "DELETE":
        return delete_product(request,product_id)
    
    #handling unsupported methods
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)

