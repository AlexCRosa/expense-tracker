from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone


class User(AbstractUser):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.username


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Account(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TYPE_CHOICES = [
        ("expense", "Expense"),
        ("income", "Income"),
        ("payment", "Payment"),
        ("savings", "Savings"),
        ("fee", "Fee"),
        ("tax", "Tax"),
        ("internal", "Internal"),
    ]
    SPENDING_TYPES = ["expense", "fee", "tax"]
    NOT_ON_EXPENSE_PAGE = ["income", "internal"]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transactions"
    )
    account = models.ForeignKey(
        "Account", on_delete=models.PROTECT, related_name="transactions"
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="expense")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    savings_goal = models.ForeignKey(
        "SavingsGoal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contributions",
    )
    description = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.now)
    reviewed = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_transactions",
    )

    def save(self, *args, **kwargs):
        """Money in is positive, money out is negative, except internal moves."""
        if self.type == "income":
            self.amount = abs(self.amount)
        elif self.type != "internal":
            self.amount = -abs(self.amount)
        super().save(*args, **kwargs)

    @property
    def absolute_amount(self):
        """The amount without its sign, for pages that already say which way it went."""
        return abs(self.amount)

    def __str__(self):
        return f"{self.amount} - {self.category} on {self.date}"


class BudgetQuerySet(models.QuerySet):
    def with_value_spent(self, start, end):
        """Sums the owner's spending in the budget's category between two dates."""
        return self.annotate(
            value_spent=-Coalesce(
                Sum(
                    "category__transactions__amount",
                    filter=Q(
                        category__transactions__user=F("user"),
                        category__transactions__type__in=Transaction.SPENDING_TYPES,
                        category__transactions__date__gte=start,
                        category__transactions__date__lte=end,
                    ),
                ),
                Value(0, output_field=models.DecimalField()),
            )
        ).annotate(budget_available=F("amount") - F("value_spent"))


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    objects = BudgetQuerySet.as_manager()

    class Meta:
        unique_together = ["user", "category"]

    def __str__(self):
        return f"{self.category} budget: {self.amount}"


class SavingsGoalQuerySet(models.QuerySet):
    def with_saved_amount(self):
        """Starting amount plus the savings filed against the goal, stored negative."""
        return self.annotate(
            saved_amount=F("current_amount")
            - Coalesce(
                Sum(
                    "contributions__amount",
                    filter=Q(
                        contributions__type="savings",
                        contributions__date__gte=F("created_at"),
                        contributions__date__lte=F("deadline"),
                    ),
                ),
                Value(0, output_field=models.DecimalField()),
            )
        ).annotate(amount_to_goal=F("target_amount") - F("saved_amount"))


class SavingsGoal(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="savings_goals"
    )
    goal_name = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateField(default=timezone.now)
    deadline = models.DateField()

    objects = SavingsGoalQuerySet.as_manager()

    @property
    def days_to_deadline(self):
        return (self.deadline - timezone.now().date()).days

    def __str__(self):
        return f"{self.goal_name} - {self.current_amount}/{self.target_amount}"
