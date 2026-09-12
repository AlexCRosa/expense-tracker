import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q, Sum
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from .forms import (
    AccountForm,
    BudgetForm,
    CategoryForm,
    ExpenseForm,
    IncomeForm,
    ReviewForm,
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

        # Fall back to the current month when the query params are absent
        today = timezone.now()
        month = int(self.request.GET.get("month") or today.month)
        year = int(self.request.GET.get("year") or today.year)

        context["month_choices"] = [(i, calendar.month_name[i]) for i in range(1, 13)]
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
        savings_goals = self.filter_by_person(SavingsGoal.objects.with_saved_amount())
        for goal in savings_goals:
            goal.percentage_achieved = (
                (goal.saved_amount / goal.target_amount) * 100
                if goal.target_amount
                else 0
            )
        context["savings_goals"] = savings_goals

        # Budgets Overview for the selected month/year
        last_day = calendar.monthrange(year, month)[1]
        context["budgets"] = self.filter_by_person(
            Budget.objects.select_related("category")
        ).with_value_spent(date(year, month, 1), date(year, month, last_day))

        # Internal moves cancel between their legs, so every amount counts in the balance
        totals = month_transactions.aggregate(
            income=Sum("amount", filter=Q(type="income")),
            spent=Sum("amount", filter=Q(type__in=Transaction.SPENDING_TYPES)),
            balance=Sum("amount"),
        )
        context["total_income"] = totals["income"] or 0
        context["total_expenses"] = -(totals["spent"] or 0)
        context["balance"] = totals["balance"] or 0

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


# Review Views
class ReviewListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "core/review_list.html"
    context_object_name = "transactions"

    def get_queryset(self):
        self.showing_all = self.request.GET.get("show") == "all"
        transactions = Transaction.objects.select_related(
            "user", "account", "category", "reviewed_by"
        ).order_by("-date", "-id")
        if not self.showing_all:
            transactions = transactions.filter(reviewed=False)
        return transactions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transactions = context["transactions"]

        # One row per transaction would otherwise query the dropdowns once each
        accounts = [(account.pk, str(account)) for account in Account.objects.all()]
        categories = [("", "---------")] + [
            (category.pk, str(category)) for category in Category.objects.all()
        ]
        for transaction in transactions:
            form = ReviewForm(instance=transaction)
            form.fields["account"].choices = accounts
            form.fields["category"].choices = categories
            transaction.form = form

        context["showing_all"] = self.showing_all
        context["unreviewed_count"] = (
            Transaction.objects.filter(reviewed=False).count()
            if self.showing_all
            else len(transactions)
        )
        return context


class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = ReviewForm

    def form_valid(self, form):
        form.instance.reviewed = True
        form.instance.reviewed_at = timezone.now()
        form.instance.reviewed_by = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.request.GET.get("show") == "all":
            return f"{reverse_lazy('core:review_list')}?show=all"
        return reverse_lazy("core:review_list")


class MarkAllReviewedView(LoginRequiredMixin, View):
    def post(self, request):
        Transaction.objects.filter(reviewed=False).update(
            reviewed=True, reviewed_at=timezone.now(), reviewed_by=request.user
        )
        return HttpResponseRedirect(reverse_lazy("core:review_list"))


# Budget Views
class BudgetListView(LoginRequiredMixin, PersonFilterMixin, ListView):
    model = Budget
    template_name = "core/budget_list.html"
    context_object_name = "budgets"

    def get_queryset(self):
        return self.filter_by_person(
            Budget.objects.select_related("category", "user")
        ).with_value_spent(F("start_date"), F("end_date"))


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
