from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("api","0004_purchase_orders"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name="Warehouse",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("code",models.CharField(max_length=20,unique=True)),("name",models.CharField(max_length=120)),("address",models.CharField(blank=True,max_length=240)),("active",models.BooleanField(default=True))]),
        migrations.CreateModel(name="WarehouseStock",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("quantity",models.IntegerField(default=0)),
            ("product",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="warehouse_stocks",to="api.product")),
            ("warehouse",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="stocks",to="api.warehouse"))],options={"unique_together":{("warehouse","product")}}),
        migrations.CreateModel(name="StockTransfer",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("reference",models.CharField(max_length=40,unique=True)),("quantity",models.PositiveIntegerField()),("status",models.CharField(choices=[("completed","Completed"),("cancelled","Cancelled")],default="completed",max_length=20)),("created_at",models.DateTimeField(auto_now_add=True)),
            ("created_by",models.ForeignKey(null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="stock_transfers",to=settings.AUTH_USER_MODEL)),
            ("from_warehouse",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="outgoing_transfers",to="api.warehouse")),
            ("product",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="warehouse_transfers",to="api.product")),
            ("to_warehouse",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="incoming_transfers",to="api.warehouse"))])]
