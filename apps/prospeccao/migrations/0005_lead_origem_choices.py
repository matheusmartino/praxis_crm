# Generated manually on 2026-02-18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prospeccao', '0004_lead_criado_por'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lead',
            name='origem',
            field=models.CharField(
                choices=[
                    ('GOOGLE', 'Google'),
                    ('INSTAGRAM', 'Instagram'),
                    ('FACEBOOK', 'Facebook'),
                    ('INDICACAO', 'Indicação'),
                    ('WHATSAPP', 'WhatsApp'),
                    ('SITE', 'Site'),
                    ('LOJA_FISICA', 'Loja física'),
                    ('OUTRO', 'Outro'),
                ],
                max_length=100,
                verbose_name='Origem',
            ),
        ),
    ]
