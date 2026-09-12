from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Account, Budget, Category, SavingsGoal, Transaction, User


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ["username", "email", "first_name", "last_name", "date_joined"]

    # Modify fieldsets to avoid duplicates
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["date", "amount", "type", "category", "account", "user", "reviewed"]
    list_filter = ["type", "reviewed", "category", "account"]
    search_fields = ["description"]


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ["user", "category", "amount", "start_date", "end_date"]
    list_filter = ["category", "start_date", "end_date"]


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ["goal_name", "user", "target_amount", "current_amount", "deadline"]
    list_filter = ["deadline"]


admin.site.register(User, CustomUserAdmin)
