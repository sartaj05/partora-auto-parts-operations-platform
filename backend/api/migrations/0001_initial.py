from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Supplier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("contact_name", models.CharField(blank=True, max_length=120)),
                ("phone", models.CharField(blank=True, max_length=30)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("lead_time_days", models.PositiveIntegerField(default=3)),
                ("rating", models.DecimalField(decimal_places=1, default=4.0, max_digits=2)),
                ("active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("admin", "Admin"), ("manager", "Manager"), ("sales", "Sales"), ("store", "Store")], default="sales", max_length=20)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sku", models.CharField(max_length=40, unique=True)),
                ("name", models.CharField(max_length=160)),
                ("brand", models.CharField(max_length=80)),
                ("category", models.CharField(choices=[("auto", "Auto Parts"), ("hardware", "Hardware"), ("electrical", "Electrical")], max_length=20)),
                ("price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("stock_qty", models.IntegerField(default=0)),
                ("reorder_level", models.PositiveIntegerField(default=10)),
                ("bin_location", models.CharField(blank=True, max_length=40)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("supplier", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="products", to="api.supplier")),
            ],
        ),
        migrations.CreateModel(
            name="Quotation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quote_no", models.CharField(max_length=30, unique=True)),
                ("customer_name", models.CharField(max_length=140)),
                ("customer_company", models.CharField(blank=True, max_length=140)),
                ("total", models.DecimalField(decimal_places=2, max_digits=12)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("sent", "Sent"), ("approved", "Approved"), ("expired", "Expired")], default="draft", max_length=20)),
                ("valid_until", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="quotations", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="StockMovement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("movement_type", models.CharField(choices=[("in", "Stock In"), ("out", "Stock Out"), ("adjustment", "Adjustment")], max_length=20)),
                ("quantity", models.IntegerField()),
                ("reference", models.CharField(blank=True, max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="movements", to="api.product")),
            ],
        ),
    ]
