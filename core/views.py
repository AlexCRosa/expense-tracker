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
    BudgetForm,
    CategoryForm,
    ExpenseForm,
    IncomeForm,
    SavingsGoalForm,
)
from .models import Budget, Category, Expense, Income, SavingsGoal, User


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


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

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

        # Last expenses across everyone, so the name on each line means something
        context["last_expenses"] = (
            Expense.objects.filter(date__month=month, date__year=year)
            .select_related("user", "category")
            .order_by("-date")[:3]
        )

        # Spending for the selected month grouped by the person who added it
        context["spending_by_user"] = (
            Expense.objects.filter(date__year=year, date__month=month)
            .values("user__username")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        context["household_spending"] = (
            Expense.objects.filter(date__year=year, date__month=month).aggregate(
                Sum("amount")
            )["amount__sum"]
            or 0
        )

        # Savings Goals (no filtering by month/year)
        savings_goals = SavingsGoal.objects.filter(user=user)
        for goal in savings_goals:
            goal.percentage_achieved = (
                (goal.current_amount / goal.target_amount) * 100
                if goal.target_amount
                else 0
            )
            goal.days_to_deadline = (goal.deadline - timezone.now().date()).days
        context["savings_goals"] = savings_goals

        # Budgets Overview for the selected month/year
        context["budgets"] = (
            Budget.objects.filter(user=user)
            .select_related("category")
            .annotate(
                value_spent=Coalesce(
                    Sum(
                        "category__expenses__amount",
                        filter=Q(
                            category__expenses__date__month=month,
                            category__expenses__date__year=year,
                        ),
                    ),
                    Value(0, output_field=DecimalField()),
                )
            )
            .annotate(remaining_budget=F("amount") - F("value_spent"))
        )

        total_income = (
            Income.objects.filter(
                user=user, date__year=year, date__month=month
            ).aggregate(Sum("amount"))["amount__sum"]
            or 0
        )
        context["total_income"] = total_income

        total_expenses = (
            Expense.objects.filter(
                user=user, date__year=year, date__month=month
            ).aggregate(Sum("amount"))["amount__sum"]
            or 0
        )

        context["balance"] = total_income - total_expenses

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


# Expense Views
class ExpenseListView(LoginRequiredMixin, PersonFilterMixin, ListView):
    model = Expense
    template_name = "core/expense_list.html"

    def get_queryset(self):
        return self.filter_by_person(Expense.objects.select_related("category"))


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
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
    model = Expense
    form_class = ExpenseForm
    template_name = "core/expense_form.html"
    success_url = reverse_lazy("core:expense_list")


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = "core/expense_confirm_delete.html"
    success_url = reverse_lazy("core:expense_list")


# Income Views
class IncomeListView(LoginRequiredMixin, PersonFilterMixin, ListView):
    model = Income
    template_name = "core/income_list.html"

    def get_queryset(self):
        return self.filter_by_person(Income.objects.all())


class IncomeCreateView(LoginRequiredMixin, CreateView):
    model = Income
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
    model = Income
    form_class = IncomeForm
    template_name = "core/income_form.html"
    success_url = reverse_lazy("core:income_list")


class IncomeDeleteView(LoginRequiredMixin, DeleteView):
    model = Income
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
                value_spent=Coalesce(
                    Sum(
                        "category__expenses__amount",
                        filter=Q(
                            category__expenses__user=F("user"),
                            category__expenses__date__gte=F("start_date"),
                            category__expenses__date__lte=F("end_date"),
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
        return self.filter_by_person(SavingsGoal.objects.select_related("user"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        savings_goals = self.get_queryset()
        for goal in savings_goals:
            goal.amount_to_goal = goal.target_amount - goal.current_amount

            days_to_go = (goal.deadline - date.today()).days
            goal.remaining_days = (
                f"{days_to_go} days to go" if days_to_go > 0 else "Deadline passed"
            )
        context["savings_goals"] = savings_goals
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
