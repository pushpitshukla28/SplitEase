from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_friendrequest'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Settlement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('payee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='settlements_received',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('payer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='settlements_paid',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('trip', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='settlements',
                    to='core.trip',
                )),
            ],
        ),
    ]
