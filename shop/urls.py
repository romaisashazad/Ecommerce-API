from django.urls import path   # path -> defines one URL pattern
from . import views             # getting the whole py file as views, so we can get views.getallprod

urlpatterns = [

    path("products/", views.list_products, name = "list_products"), 
    path("products/create/", views.create_product, name="create_product"),  # POST
    path("products/lookup/", views.retrieve_product_by_query, name="retrieve_product_by_query"), # specific URL segment should come first
    path("products/<str:product_id>/", views.product_detail_router, name="product_detail_router"), # generic catch-all pattern
]
