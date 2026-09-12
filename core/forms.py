from django import forms

from .models import Account, Budget, Category, SavingsGoal, Transaction


class ExpenseForm(forms.ModelForm):
    """Money going out: the user types a positive amount and the model signs it."""

    class Meta:
        model = Transaction
        fields = [
            "account",
            "type",
            "amount",
            "category",
            "savings_goal",
            "description",
            "date",
        ]
        widgets = {
            "account": forms.Select(attrs={"class": "form-select"}),
            "type": forms.Select(attrs={"class": "form-select"}),
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
        self.fields["type"].choices = [
            (value, label)
            for value, label in Transaction.TYPE_CHOICES
            if value not in ("income", "internal")
        ]
        if self.instance.pk:
            self.initial["amount"] = self.instance.absolute_amount


class IncomeForm(forms.ModelForm):
    """Money coming in, always typed as income."""

    class Meta:
        model = Transaction
        fields = ["account", "amount", "category", "description", "date"]
        widgets = {
            "account": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
        }

    def save(self, commit=True):
        self.instance.type = "income"
        return super().save(commit)


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


class ReviewForm(forms.ModelForm):
    """The three fields a bank import is most likely to have got wrong."""

    class Meta:
        model = Transaction
        fields = ["account", "type", "category"]
        widgets = {
            "account": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "type": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "category": forms.Select(attrs={"class": "form-select form-select-sm"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A table row cannot hold a form tag, so the fields point at one by id
        for field in self.fields.values():
            field.widget.attrs["form"] = f"review-{self.instance.pk}"
