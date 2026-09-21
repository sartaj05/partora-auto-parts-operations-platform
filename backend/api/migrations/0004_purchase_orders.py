from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("api","0003_vehiclefitment"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name="PurchaseOrder", fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("po_no",models.CharField(max_length=30,unique=True)),
            ("status",models.CharField(choices=[("draft","Draft"),("approved","Approved"),("ordered","Ordered"),("partial","Partially received"),("received","Received")],default="draft",max_length=20)),
            ("expected_date",models.DateField(blank=True,null=True)),
            ("total",models.DecimalField(decimal_places=2,default=0,max_digits=14)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("created_by",models.ForeignKey(null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="purchase_orders",to=settings.AUTH_USER_MODEL)),
            ("supplier",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="purchase_orders",to="api.supplier")),
        ]),
        migrations.CreateModel(name="PurchaseOrderItem", fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("quantity",models.PositiveIntegerField()),
            ("unit_cost",models.DecimalField(decimal_places=2,max_digits=12)),
            ("received_qty",models.PositiveIntegerField(default=0)),
            ("product",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="purchase_order_items",to="api.product")),
            ("purchase_order",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="items",to="api.purchaseorder")),
        ])
    ]
