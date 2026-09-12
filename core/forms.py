from django import forms

from .models import Account, Budget, Category, Expense, Income, SavingsGoal


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["amount", "category", "savings_goal", "description", "date"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "savings_goal": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        savings = Category.objects.filter(name="Savings").first()
        self.savings_category_id = savings.pk if savings else ""


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ["amount", "description", "date"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
        }


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ["category", "amount", "start_date", "end_date"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
            "end_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
        }


class SavingsGoalForm(forms.ModelForm):
    class Meta:
        model = SavingsGoal
        fields = ["goal_name", "target_amount", "current_amount", "deadline"]
        widgets = {
            "goal_name": forms.TextInput(attrs={"class": "form-control"}),
            "target_amount": forms.NumberInput(attrs={"class": "form-control"}),
            "current_amount": forms.NumberInput(attrs={"class": "form-control"}),
            "deadline": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": "form-control"})}
