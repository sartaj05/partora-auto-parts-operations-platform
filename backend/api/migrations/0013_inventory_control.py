from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("api", "0012_returns_rma")]

    operations = [
        migrations.CreateModel(
            name="InventoryCount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference", models.CharField(max_length=30, unique=True)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("submitted", "Submitted"), ("approved", "Approved")], default="draft", max_length=20)),
                ("notes", models.CharField(blank=True, max_length=300)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="inventory_count_approvals", to=settings.AUTH_USER_MODEL)),
                ("counted_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="inventory_counts", to=settings.AUTH_USER_MODEL)),
                ("warehouse", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="inventory_counts", to="api.warehouse")),
            ],
        ),
        migrations.CreateModel(
            name="InventoryCountLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("expected_qty", models.IntegerField()),
                ("counted_qty", models.IntegerField()),
                ("variance", models.IntegerField(default=0)),
                ("inventory_count", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lines", to="api.inventorycount")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="inventory_count_lines", to="api.product")),
            ],
        ),
        migrations.CreateModel(
            name="ProductLot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("lot_no", models.CharField(max_length=80)),
                ("serial_no", models.CharField(blank=True, max_length=100)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("received_at", models.DateField(default=django.utils.timezone.localdate)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lots", to="api.product")),
                ("warehouse", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="product_lots", to="api.warehouse")),
            ],
        ),
    ]
