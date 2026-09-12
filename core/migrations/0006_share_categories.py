from django.db import migrations, models


def merge_duplicate_categories(apps, schema_editor):
    """Point expenses and budgets at one category per name, then drop the extras."""
    Category = apps.get_model("core", "Category")
    Expense = apps.get_model("core", "Expense")
    Budget = apps.get_model("core", "Budget")

    for name in Category.objects.values_list("name", flat=True).distinct():
        duplicates = list(Category.objects.filter(name=name).order_by("user_id", "id"))
        keeper = duplicates[0]
        for extra in duplicates[1:]:
            Expense.objects.filter(category=extra).update(category=keeper)
            Budget.objects.filter(category=extra).update(category=keeper)
            if not keeper.description and extra.description:
                keeper.description = extra.description
                keeper.save()
            extra.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_alter_income_date_alter_income_description"),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_categories, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name="category",
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name="category",
            name="name",
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.RemoveField(
            model_name="category",
            name="user",
        ),
    ]
