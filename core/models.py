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


class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="expenses"
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

    def __str__(self):
        return f"{self.amount} - {self.category} on {self.date}"


class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="incomes")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(
        verbose_name="Source of Income", blank=True, null=True
    )
    date = models.DateField(verbose_name="Date of Credit", default=timezone.now)

    def __str__(self):
        return f"{self.amount} on {self.date}"


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.category} budget: {self.amount}"


class SavingsGoalQuerySet(models.QuerySet):
    def with_saved_amount(self):
        """Adds the starting amount to the savings filed against the goal in its window."""
        return self.annotate(
            saved_amount=F("current_amount")
            + Coalesce(
                Sum(
                    "contributions__amount",
                    filter=Q(
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

    def __str__(self):
        return f"{self.goal_name} - {self.current_amount}/{self.target_amount}"
