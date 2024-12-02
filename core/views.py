from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Category, Expense, Income, Budget, SavingsGoal
from django.utils import timezone
from django.db.models import Sum, F, Value, DecimalField
from django.db.models.functions import Coalesce



# Category Views
class CategoryListView(ListView):
    model = Category
    template_name = 'core/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        """
        Show user-owned categories and default categories that the user has not customized.
        """
        user_categories = Category.objects.filter(user=self.request.user)
        default_categories = Category.objects.filter(user=None).exclude(
            name__in=user_categories.values_list('name', flat=True)
        )
        return user_categories | default_categories


class CategoryCreateView(CreateView):
    model = Category
    fields = ['name', 'description']
    template_name = 'core/category_form.html'

    def form_valid(self, form):
        """
        Ensure the category is unique per user and does not conflict with default categories.
        """
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


class CategoryUpdateView(UpdateView):
    model = Category
    fields = ['name', 'description']  # Include both fields
    template_name = 'core/category_form.html'

    def get_form(self, form_class=None):
        """
        Customize the form to remove the 'name' field for default categories.
        """
        form = super().get_form(form_class)
        if self.object.user is None:  # Default category
            form.fields.pop('name')  # Remove 'name' field for default categories
        return form

    def form_valid(self, form):
        """
        Handle saving changes:
        - For default categories, create a user-specific copy.
        - For user-owned categories, save changes normally.
        """
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
        """
        Limit access to:
        - Categories owned by the user.
        - Default categories.
        """
        return Category.objects.filter(user=self.request.user) | Category.objects.filter(user=None)

    def get_success_url(self):
        """
        Redirect to the category list after editing.
        """
        return reverse_lazy('core:category_list')


class CategoryDeleteView(DeleteView):
    model = Category
    template_name = 'core/category_confirm_delete.html'
    success_url = reverse_lazy('core:category_list')


# Expense Views
class ExpenseListView(ListView):
    model = Expense
    template_name = 'core/expense_list.html'

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)


class ExpenseCreateView(CreateView):
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


class ExpenseUpdateView(UpdateView):
    model = Expense
    fields = ['amount', 'category', 'description', 'date']
    template_name = 'core/expense_form.html'
    success_url = reverse_lazy('core:expense_list')


class ExpenseDeleteView(DeleteView):
    model = Expense
    template_name = 'core/expense_confirm_delete.html'
    success_url = reverse_lazy('core:expense_list')


# Income Views
class IncomeListView(ListView):
    model = Income
    template_name = 'core/income_list.html'

    def get_queryset(self):
        return Income.objects.filter(user=self.request.user)


class IncomeCreateView(CreateView):
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


class IncomeUpdateView(UpdateView):
    model = Income
    fields = ['amount', 'description', 'date']
    template_name = 'core/income_form.html'
    success_url = reverse_lazy('core:income_list')


class IncomeDeleteView(DeleteView):
    model = Income
    template_name = 'core/income_confirm_delete.html'
    success_url = reverse_lazy('core:income_list')


# Budget Views
class BudgetListView(ListView):
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


class BudgetCreateView(CreateView):
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


class BudgetUpdateView(UpdateView):
    model = Budget
    fields = ['category', 'amount', 'start_date', 'end_date']
    template_name = 'core/budget_form.html'
    success_url = reverse_lazy('core:budget_list')


class BudgetDeleteView(DeleteView):
    model = Budget
    template_name = 'core/budget_confirm_delete.html'
    success_url = reverse_lazy('core:budget_list')


# SavingsGoal Views
from datetime import date

class SavingsGoalListView(ListView):
    model = SavingsGoal
    template_name = 'core/savings_goal_list.html'
    context_object_name = 'savings_goals'

    def get_queryset(self):
        """
        Show savings goals for the current user.
        """
        return SavingsGoal.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """
        Add remaining days to deadline in context.
        """
        context = super().get_context_data(**kwargs)
        savings_goals = self.get_queryset()
        for goal in savings_goals:
            goal.amount_to_goal = goal.target_amount - goal.current_amount

            days_to_go = (goal.deadline - date.today()).days
            goal.remaining_days = f"{days_to_go} days to go" if days_to_go > 0 else "Deadline passed"
        context['savings_goals'] = savings_goals
        return context


class SavingsGoalCreateView(CreateView):
    model = SavingsGoal
    fields = ['goal_name', 'target_amount', 'current_amount', 'deadline']
    template_name = 'core/savings_goal_form.html'
    success_url = reverse_lazy('core:savings_goal_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class SavingsGoalUpdateView(UpdateView):
    model = SavingsGoal
    fields = ['goal_name', 'target_amount', 'current_amount', 'deadline']
    template_name = 'core/savings_goal_form.html'
    success_url = reverse_lazy('core:savings_goal_list')


class SavingsGoalDeleteView(DeleteView):
    model = SavingsGoal
    template_name = 'core/savings_goal_confirm_delete.html'
    success_url = reverse_lazy('core:savings_goal_list')
