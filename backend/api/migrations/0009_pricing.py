from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[("api","0008_customer")]
    operations=[
        migrations.AddField(model_name="product",name="cost_price",field=models.DecimalField(decimal_places=2,default=0,max_digits=12)),
        migrations.AddField(model_name="product",name="wholesale_price",field=models.DecimalField(decimal_places=2,default=0,max_digits=12)),
        migrations.AddField(model_name="product",name="dealer_price",field=models.DecimalField(decimal_places=2,default=0,max_digits=12)),
        migrations.CreateModel(name="PriceRule",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("name",models.CharField(max_length=120)),("customer_type",models.CharField(choices=[("retail","Retail"),("dealer","Dealer"),("fleet","Fleet"),("workshop","Workshop")],default="dealer",max_length=20)),("min_qty",models.PositiveIntegerField(default=1)),("discount_percent",models.DecimalField(decimal_places=2,default=0,max_digits=5)),("active",models.BooleanField(default=True)),("created_at",models.DateTimeField(auto_now_add=True))])]
