from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Category, Expense, Income, Budget, SavingsGoal
from django.urls import reverse_lazy

from django.http import HttpResponseRedirect
from django.contrib import messages

from django.utils import timezone
from datetime import date, datetime
import calendar

from django.db.models import Sum, F, Q, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce, TruncMonth

from django.db import connection


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get the selected month from the query params, default to the current month
        selected_month = self.request.GET.get('month')
        selected_year = self.request.GET.get('year')

        # Fallback to current month/year if none is selected
        today = timezone.now()
        current_month = today.month
        current_year = today.year

        month = int(selected_month) if selected_month else current_month
        year = int(selected_year) if selected_year else current_year

        # Add month names to the context
        context['month_choices'] = [(i, calendar.month_name[i]) for i in range(1, 13)]
        context['current_month'] = current_month
        context['current_year'] = current_year
        context['selected_month'] = month
        context['selected_year'] = year

        # Other context data...
        context['last_expenses'] = Expense.objects.filter(
            user=user,
            date__month=month,
            date__year=year
        ).order_by('-date')[:3]

        # Savings Goals (no filtering by month/year)
        savings_goals = SavingsGoal.objects.filter(user=user)
        for goal in savings_goals:
            goal.percentage_achieved = (goal.current_amount / goal.target_amount) * 100 if goal.target_amount else 0
            goal.days_to_deadline = (goal.deadline - timezone.now().date()).days
        context['savings_goals'] = savings_goals

        # Budgets Overview for the selected month/year
        budgets = Budget.objects.filter(user=user).annotate(
            value_spent=Sum(
                'category__expenses__amount',
                filter=Q(category__expenses__date__month=month, category__expenses__date__year=year)
            ),
            remaining_budget=ExpressionWrapper(
                F('amount') - Coalesce(Sum('category__expenses__amount', filter=Q(
                    category__expenses__date__month=month,
                    category__expenses__date__year=year
                )), Value(0)),
                output_field=DecimalField()
            )
        )
        context['budgets'] = budgets

        # Total Income for the selected month/year
        context['total_income'] = Income.objects.filter(
            user=user,
            date__year=year,
            date__month=month
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        return context


# Category Views
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'core/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        user_categories = Category.objects.filter(user=self.request.user)
        default_categories = Category.objects.filter(user=None).exclude(
            name__in=user_categories.values_list('name', flat=True)
        )
        return user_categories | default_categories


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    fields = ['name', 'description']
    template_name = 'core/category_form.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        if Category.objects.filter(name=form.instance.name, user=self.request.user).exists():
            messages.error(self.request, "You already have a category with this name.")
            return self.form_invalid(form)
        if Category.objects.filter(name=form.instance.name, user=None).exists():
            messages.error(self.request, "This name is reserved for a default category.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('core:category_list')


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    fields = ['name', 'description']  # Include both fields
    template_name = 'core/category_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.object.user is None:  # Default category
            form.fields.pop('name')  # Remove 'name' field for default categories
        return form

    def form_valid(self, form):
        category = self.object
        if category.user is None:  # Default category
            # Create a user-specific copy with the updated description
            Category.objects.create(
                user=self.request.user,
                name=category.name,
                description=form.cleaned_data['description']
            )
        else:
            # Save changes for user-owned categories
            form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user) | Category.objects.filter(user=None)

    def get_success_url(self):
        return reverse_lazy('core:category_list')


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'core/category_confirm_delete.html'
    success_url = reverse_lazy('core:category_list')


# Expense Views
class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'core/expense_list.html'

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    fields = ['amount', 'category', 'description', 'date']
    template_name = 'core/expense_form.html'
    success_url = reverse_lazy('core:expense_list')

    def form_valid(self, form):
        # Set the user of the expense to the logged-in user
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial['date'] = timezone.now().date()
        return initial


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    fields = ['amount', 'category', 'description', 'date']
    template_name = 'core/expense_form.html'
    success_url = reverse_lazy('core:expense_list')


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'core/expense_confirm_delete.html'
    success_url = reverse_lazy('core:expense_list')


# Income Views
class IncomeListView(LoginRequiredMixin, ListView):
    model = Income
    template_name = 'core/income_list.html'

    def get_queryset(self):
        return Income.objects.filter(user=self.request.user)


class IncomeCreateView(LoginRequiredMixin, CreateView):
    model = Income
    fields = ['amount', 'description', 'date']
    template_name = 'core/income_form.html'
    success_url = reverse_lazy('core:income_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial['date'] = timezone.now().date()
        return initial


class IncomeUpdateView(LoginRequiredMixin, UpdateView):
    model = Income
    fields = ['amount', 'description', 'date']
    template_name = 'core/income_form.html'
    success_url = reverse_lazy('core:income_list')


class IncomeDeleteView(LoginRequiredMixin, DeleteView):
    model = Income
    template_name = 'core/income_confirm_delete.html'
    success_url = reverse_lazy('core:income_list')


# Budget Views
class BudgetListView(LoginRequiredMixin, ListView):
    model = Budget
    template_name = 'core/budget_list.html'

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        budgets = self.get_queryset()  # Get only the budgets of the current user
        budgets_data = []
        for budget in budgets:
            # Sum expenses of the current user within the budget's date range
            value_spent = budget.category.expenses.filter(
                user=self.request.user,  # Filter by the current user
                date__range=(budget.start_date, budget.end_date)
            ).aggregate(
                total=Coalesce(Sum('amount', output_field=DecimalField()), Value(0, output_field=DecimalField()))
            )['total']

            budgets_data.append({
                'id': budget.id,
                'category': budget.category.name,
                'budget_defined': budget.amount,
                'value_spent': value_spent,
                'budget_available': budget.amount - value_spent,
                'start_date': budget.start_date,
                'end_date': budget.end_date,
            })
        context['budgets_data'] = budgets_data
        return context


class BudgetCreateView(LoginRequiredMixin, CreateView):
    model = Budget
    fields = ['category', 'amount', 'start_date', 'end_date']
    template_name = 'core/budget_form.html'
    success_url = reverse_lazy('core:budget_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        if Budget.objects.filter(user=self.request.user, category=form.cleaned_data['category']).exists():
            messages.error(self.request, "You already have a budget for this category.")
            return self.form_invalid(form)

        return super().form_valid(form)
    
    def get_initial(self):
        initial = super().get_initial()
        initial['start_date'] = date(timezone.now().year, timezone.now().month, 1)
        initial['end_date'] = date(timezone.now().year, timezone.now().month, calendar.monthrange(timezone.now().year, timezone.now().month)[1])
        return initial


class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    model = Budget
    fields = ['category', 'amount', 'start_date', 'end_date']
    template_name = 'core/budget_form.html'
    success_url = reverse_lazy('core:budget_list')


class BudgetDeleteView(LoginRequiredMixin, DeleteView):
    model = Budget
    template_name = 'core/budget_confirm_delete.html'
    success_url = reverse_lazy('core:budget_list')


# SavingsGoal Views
class SavingsGoalListView(LoginRequiredMixin, ListView):
    model = SavingsGoal
    template_name = 'core/savings_goal_list.html'
    context_object_name = 'savings_goals'

    def get_queryset(self):
        return SavingsGoal.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        savings_goals = self.get_queryset()
        for goal in savings_goals:
            goal.amount_to_goal = goal.target_amount - goal.current_amount

            days_to_go = (goal.deadline - date.today()).days
            goal.remaining_days = f"{days_to_go} days to go" if days_to_go > 0 else "Deadline passed"
        context['savings_goals'] = savings_goals
        return context


class SavingsGoalCreateView(LoginRequiredMixin, CreateView):
    model = SavingsGoal
    fields = ['goal_name', 'target_amount', 'current_amount', 'deadline']
    template_name = 'core/savings_goal_form.html'
    success_url = reverse_lazy('core:savings_goal_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class SavingsGoalUpdateView(LoginRequiredMixin, UpdateView):
    model = SavingsGoal
    fields = ['goal_name', 'target_amount', 'current_amount', 'deadline']
    template_name = 'core/savings_goal_form.html'
    success_url = reverse_lazy('core:savings_goal_list')


class SavingsGoalDeleteView(LoginRequiredMixin, DeleteView):
    model = SavingsGoal
    template_name = 'core/savings_goal_confirm_delete.html'
    success_url = reverse_lazy('core:savings_goal_list')
