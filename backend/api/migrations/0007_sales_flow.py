from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("api","0006_product_reorder_qty"),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name="SalesOrder",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("order_no",models.CharField(max_length=30,unique=True)),("customer_name",models.CharField(max_length=140)),("customer_company",models.CharField(blank=True,max_length=140)),("total",models.DecimalField(decimal_places=2,max_digits=14)),("status",models.CharField(choices=[("confirmed","Confirmed"),("fulfilled","Fulfilled"),("cancelled","Cancelled")],default="confirmed",max_length=20)),("created_at",models.DateTimeField(auto_now_add=True)),
            ("created_by",models.ForeignKey(null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="sales_orders",to=settings.AUTH_USER_MODEL)),("quotation",models.OneToOneField(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="sales_order",to="api.quotation"))]),
        migrations.CreateModel(name="Invoice",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("invoice_no",models.CharField(max_length=30,unique=True)),("total",models.DecimalField(decimal_places=2,max_digits=14)),("status",models.CharField(choices=[("issued","Issued"),("paid","Paid"),("overdue","Overdue"),("cancelled","Cancelled")],default="issued",max_length=20)),("due_date",models.DateField()),("created_at",models.DateTimeField(auto_now_add=True)),("sales_order",models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,related_name="invoice",to="api.salesorder"))])]
