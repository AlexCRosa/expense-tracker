import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import (
    AccountForm,
    BudgetForm,
    CategoryForm,
    ExpenseForm,
    IncomeForm,
    SavingsGoalForm,
)
from .models import Account, Budget, Category, SavingsGoal, Transaction, User


class PersonFilterMixin:
    """Narrows a queryset to one person when the person query param is set."""

    def get_selected_person(self):
        person = self.request.GET.get("person", "")
        return person if person.isdigit() else ""

    def filter_by_person(self, queryset):
        person = self.get_selected_person()
        return queryset.filter(user_id=person) if person else queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["people"] = User.objects.order_by("username")
        context["selected_person"] = self.get_selected_person()
        return context


class DashboardView(LoginRequiredMixin, PersonFilterMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the selected month from the query params, default to the current month
        selected_month = self.request.GET.get("month")
        selected_year = self.request.GET.get("year")

        # Fallback to current month/year if none is selected
        today = timezone.now()
        current_month = today.month
        current_year = today.year

        month = int(selected_month) if selected_month else current_month
        year = int(selected_year) if selected_year else current_year

        # Add month names to the context
        context["month_choices"] = [(i, calendar.month_name[i]) for i in range(1, 13)]
        context["current_month"] = current_month
        context["current_year"] = current_year
        context["selected_month"] = month
        context["selected_year"] = year

        month_transactions = self.filter_by_person(
            Transaction.objects.filter(date__month=month, date__year=year)
        )
        spending = month_transactions.filter(type__in=Transaction.SPENDING_TYPES)

        context["last_expenses"] = spending.select_related("user", "category").order_by(
            "-date"
        )[:3]

        # Spending for the selected month grouped by the person who added it
        context["spending_by_user"] = (
            spending.values("user__first_name")
            .annotate(total=-Sum("amount"))
            .order_by("-total")
        )

        # Savings Goals (no filtering by month/year)
        savings_goals = self.filter_by_person(
            SavingsGoal.objects.with_saved_amount().select_related("user")
        )
        for goal in savings_goals:
            goal.percentage_achieved = (
                (goal.saved_amount / goal.target_amount) * 100
                if goal.target_amount
                else 0
            )
            goal.days_to_deadline = (goal.deadline - timezone.now().date()).days
        context["savings_goals"] = savings_goals

        # Budgets Overview for the selected month/year
        context["budgets"] = (
            self.filter_by_person(Budget.objects.select_related("category"))
            .annotate(
                value_spent=-Coalesce(
                    Sum(
                        "category__transactions__amount",
                        filter=Q(
                            category__transactions__user=F("user"),
                            category__transactions__type__in=Transaction.SPENDING_TYPES,
                            category__transactions__date__month=month,
                            category__transactions__date__year=year,
                        ),
                    ),
                    Value(0, output_field=DecimalField()),
                )
            )
            .annotate(remaining_budget=F("amount") - F("value_spent"))
        )

        total_income = (
            month_transactions.filter(type="income").aggregate(Sum("amount"))[
                "amount__sum"
            ]
            or 0
        )
        context["total_income"] = total_income

        total_expenses = -(spending.aggregate(Sum("amount"))["amount__sum"] or 0)
        context["total_expenses"] = total_expenses

        # Internal moves cancel between their two legs, so every amount counts here
        context["balance"] = (
            month_transactions.aggregate(Sum("amount"))["amount__sum"] or 0
        )

        return context


# Category Views
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "core/category_list.html"
    context_object_name = "categories"


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "core/category_form.html"
    success_url = reverse_lazy("core:category_list")


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "core/category_form.html"
    success_url = reverse_lazy("core:category_list")


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = "core/category_confirm_delete.html"
    success_url = reverse_lazy("core:category_list")


# Account Views
class AccountListView(LoginRequiredMixin, ListView):
    model = Account
    template_name = "core/account_list.html"
    context_object_name = "accounts"


class AccountCreateView(LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = "core/account_form.html"
    success_url = reverse_lazy("core:account_list")


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = "core/account_form.html"
    success_url = reverse_lazy("core:account_list")


class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model = Account
    template_name = "core/account_confirm_delete.html"
    success_url = reverse_lazy("core:account_list")


# Expense Views
class ExpenseListView(LoginRequiredMixin, PersonFilterMixin, ListView):
    model = Transaction
    template_name = "core/expense_list.html"

    def get_queryset(self):
        return self.filter_by_person(
            Transaction.objects.exclude(type="income").select_related(
                "category", "account"
            )
        )


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = ExpenseForm
    template_name = "core/expense_form.html"
    success_url = reverse_lazy("core:expense_list")

    def form_valid(self, form):
        # Set the user of the expense to the logged-in user
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial["date"] = timezone.now().date()
        return initial


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = ExpenseForm
    template_name = "core/expense_form.html"
    success_url = reverse_lazy("core:expense_list")


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = "core/expense_confirm_delete.html"
    success_url = reverse_lazy("core:expense_list")


# Income Views
class IncomeListView(LoginRequiredMixin, PersonFilterMixin, ListView):
    model = Transaction
    template_name = "core/income_list.html"

    def get_queryset(self):
        return self.filter_by_person(
            Transaction.objects.filter(type="income").select_related(
                "category", "account"
            )
        )


class IncomeCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = IncomeForm
    template_name = "core/income_form.html"
    success_url = reverse_lazy("core:income_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial["date"] = timezone.now().date()
        return initial


class IncomeUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = IncomeForm
    template_name = "core/income_form.html"
    success_url = reverse_lazy("core:income_list")


class IncomeDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = "core/income_confirm_delete.html"
    success_url = reverse_lazy("core:income_list")


# Budget Views
class BudgetListView(LoginRequiredMixin, PersonFilterMixin, ListView):
    model = Budget
    template_name = "core/budget_list.html"
    context_object_name = "budgets"

    def get_queryset(self):
        # Sum each budget's own expenses within its own date range
        return self.filter_by_person(
            Budget.objects.select_related("category", "user")
            .annotate(
                value_spent=-Coalesce(
                    Sum(
                        "category__transactions__amount",
                        filter=Q(
                            category__transactions__user=F("user"),
                            category__transactions__type__in=Transaction.SPENDING_TYPES,
                            category__transactions__date__gte=F("start_date"),
                            category__transactions__date__lte=F("end_date"),
                        ),
                    ),
                    Value(0, output_field=DecimalField()),
                )
            )
            .annotate(budget_available=F("amount") - F("value_spent"))
        )


class BudgetCreateView(LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = "core/budget_form.html"
    success_url = reverse_lazy("core:budget_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        if Budget.objects.filter(
            user=self.request.user, category=form.cleaned_data["category"]
        ).exists():
            messages.error(self.request, "You already have a budget for this category.")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial["start_date"] = date(timezone.now().year, timezone.now().month, 1)
        initial["end_date"] = date(
            timezone.now().year,
            timezone.now().month,
            calendar.monthrange(timezone.now().year, timezone.now().month)[1],
        )
        return initial


class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = "core/budget_form.html"
    success_url = reverse_lazy("core:budget_list")


class BudgetDeleteView(LoginRequiredMixin, DeleteView):
    model = Budget
    template_name = "core/budget_confirm_delete.html"
    success_url = reverse_lazy("core:budget_list")


# SavingsGoal Views
class SavingsGoalListView(LoginRequiredMixin, PersonFilterMixin, ListView):
    model = SavingsGoal
    template_name = "core/savings_goal_list.html"
    context_object_name = "savings_goals"

    def get_queryset(self):
        return self.filter_by_person(
            SavingsGoal.objects.with_saved_amount().select_related("user")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for goal in context["savings_goals"]:
            days_to_go = (goal.deadline - date.today()).days
            goal.remaining_days = (
                f"{days_to_go} days to go" if days_to_go > 0 else "Deadline passed"
            )
        return context


class SavingsGoalCreateView(LoginRequiredMixin, CreateView):
    model = SavingsGoal
    form_class = SavingsGoalForm
    template_name = "core/savings_goal_form.html"
    success_url = reverse_lazy("core:savings_goal_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class SavingsGoalUpdateView(LoginRequiredMixin, UpdateView):
    model = SavingsGoal
    form_class = SavingsGoalForm
    template_name = "core/savings_goal_form.html"
    success_url = reverse_lazy("core:savings_goal_list")


class SavingsGoalDeleteView(LoginRequiredMixin, DeleteView):
    model = SavingsGoal
    template_name = "core/savings_goal_confirm_delete.html"
    success_url = reverse_lazy("core:savings_goal_list")
