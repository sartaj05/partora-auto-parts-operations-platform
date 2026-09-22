from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("api", "0014_alter_invoice_status")]

    operations = [
        migrations.AddField(model_name="purchaseorder", name="received_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.CreateModel(
            name="SupplierPriceSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("unit_cost", models.DecimalField(decimal_places=2, max_digits=12)),
                ("captured_at", models.DateTimeField(auto_now_add=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="supplier_price_snapshots", to="api.product")),
                ("source_po", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="price_snapshots", to="api.purchaseorder")),
                ("supplier", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="price_snapshots", to="api.supplier")),
            ],
        ),
    ]
