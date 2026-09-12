import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def copy_expenses_and_incomes(apps, schema_editor):
    """Folds both tables into Transaction, signing amounts as it goes."""
    Account = apps.get_model("core", "Account")
    Expense = apps.get_model("core", "Expense")
    Income = apps.get_model("core", "Income")
    Transaction = apps.get_model("core", "Transaction")

    if not Expense.objects.exists() and not Income.objects.exists():
        return

    account, _ = Account.objects.get_or_create(name="Unknown")

    for expense in Expense.objects.all():
        Transaction.objects.create(
            user=expense.user,
            account=account,
type="savings" if expense.savings_goal_id else "expense"
            amount=-abs(expense.amount),
            category=expense.category,
            savings_goal=expense.savings_goal,
            description=expense.description,
            date=expense.date,
            reviewed=True,
        )

    for income in Income.objects.all():
        Transaction.objects.create(
            user=income.user,
            account=account,
            type="income",
            amount=abs(income.amount),
            category=None,
            description=income.description,
            date=income.date,
            reviewed=True,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_account"),
    ]

    operations = [
        migrations.CreateModel(
            name="Transaction",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("expense", "Expense"),
                            ("income", "Income"),
                            ("payment", "Payment"),
                            ("savings", "Savings"),
                            ("fee", "Fee"),
                            ("tax", "Tax"),
                            ("internal", "Internal"),
                        ],
                        default="expense",
                        max_length=20,
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("description", models.TextField(blank=True, null=True)),
                ("date", models.DateField(default=django.utils.timezone.now)),
                ("reviewed", models.BooleanField(default=False)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="transactions",
                        to="core.account",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="transactions",
                        to="core.category",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_transactions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "savings_goal",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="contributions",
                        to="core.savingsgoal",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transactions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.RunPython(copy_expenses_and_incomes, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="income",
            name="user",
        ),
        migrations.DeleteModel(
            name="Expense",
        ),
        migrations.DeleteModel(
            name="Income",
        ),
    ]
