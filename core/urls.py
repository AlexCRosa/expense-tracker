from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    path('expenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('expenses/create/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<int:pk>/update/', views.ExpenseUpdateView.as_view(), name='expense_update'),
    path('expenses/<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense_delete'),

    path('incomes/', views.IncomeListView.as_view(), name='income_list'),
    path('incomes/create/', views.IncomeCreateView.as_view(), name='income_create'),
    path('incomes/<int:pk>/update/', views.IncomeUpdateView.as_view(), name='income_update'),
    path('incomes/<int:pk>/delete/', views.IncomeDeleteView.as_view(), name='income_delete'),

    path('budgets/', views.BudgetListView.as_view(), name='budget_list'),
    path('budgets/create/', views.BudgetCreateView.as_view(), name='budget_create'),
    path('budgets/<int:pk>/update/', views.BudgetUpdateView.as_view(), name='budget_update'),
    path('budgets/<int:pk>/delete/', views.BudgetDeleteView.as_view(), name='budget_delete'),

    path('savings-goals/', views.SavingsGoalListView.as_view(), name='savings_goal_list'),
    path('savings-goals/create/', views.SavingsGoalCreateView.as_view(), name='savings_goal_create'),
    path('savings-goals/<int:pk>/update/', views.SavingsGoalUpdateView.as_view(), name='savings_goal_update'),
    path('savings-goals/<int:pk>/delete/', views.SavingsGoalDeleteView.as_view(), name='savings_goal_delete'),
]
