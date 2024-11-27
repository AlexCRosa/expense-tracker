from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Category, Expense, Income, Budget, SavingsGoal


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'first_name', 'last_name', 'date_joined']
    
    # Modify fieldsets to avoid duplicates
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'description']
    search_fields = ['name']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['amount', 'user', 'category', 'description', 'date']
    list_filter = ['category', ('date', admin.DateFieldListFilter)]
    search_fields = ['description']


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['amount', 'user', 'description', 'date']
    list_filter = [('date', admin.DateFieldListFilter)]


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'amount', 'start_date', 'end_date']
    list_filter = ['category', 'start_date', 'end_date']


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ['goal_name', 'user', 'target_amount', 'current_amount', 'deadline']
    list_filter = ['deadline']


admin.site.register(User, CustomUserAdmin)