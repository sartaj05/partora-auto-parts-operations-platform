from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health),
    path("auth/login/", views.login_view),
    path("auth/me/", views.me_view),
    path("dashboard/", views.dashboard_view),
    path("inventory/", views.inventory_view),
    path("suppliers/", views.suppliers_view),
    path("quotations/", views.quotations_view),
    path("stock/", views.stock_view),
    path("barcodes/", views.barcodes_view),
    path("barcodes/lookup/", views.barcode_lookup_view),
    path("fitments/", views.fitments_view),
    path("purchase-orders/", views.purchase_orders_view),
    path("warehouses/", views.warehouses_view),
]
