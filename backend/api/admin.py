from django.contrib import admin
from .models import Product, Profile, Quotation, StockMovement, Supplier

admin.site.register(Profile)
admin.site.register(Product)
admin.site.register(Supplier)
admin.site.register(Quotation)
admin.site.register(StockMovement)
from .models import VehicleFitment
admin.site.register(VehicleFitment)
from .models import PurchaseOrder, PurchaseOrderItem
admin.site.register(PurchaseOrder)
admin.site.register(PurchaseOrderItem)
from .models import Warehouse, WarehouseStock, StockTransfer
admin.site.register(Warehouse)
admin.site.register(WarehouseStock)
admin.site.register(StockTransfer)
