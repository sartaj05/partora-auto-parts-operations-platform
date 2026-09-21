from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[("api","0005_warehouses")]
    operations=[migrations.AddField(model_name="product",name="reorder_qty",field=models.PositiveIntegerField(default=25))]
