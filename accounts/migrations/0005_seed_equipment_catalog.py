from django.db import migrations


def seed_equipment_catalog(apps, schema_editor):
    Equipment = apps.get_model('accounts', 'Equipment')

    # Preserve any catalog already configured in the target database.
    if Equipment.objects.exists():
        return

    Equipment.objects.bulk_create([
        Equipment(
            name='Микроскоп',
            category='lab',
            total_quantity=3,
            available_quantity=3,
        ),
        Equipment(
            name='Ноутбуки для занятий',
            category='computer',
            total_quantity=5,
            available_quantity=5,
        ),
        Equipment(
            name='Проекторы',
            category='presentation',
            total_quantity=7,
            available_quantity=7,
        ),
    ])


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0004_equipment_equipmentrequest_equipmentrequestevent'),
    ]

    operations = [
        migrations.RunPython(seed_equipment_catalog, migrations.RunPython.noop),
    ]
