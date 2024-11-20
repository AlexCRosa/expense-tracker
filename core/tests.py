from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date

from core.models import Expense, Income, Category, Budget, SavingsGoal


class UserManagersTest(TestCase):
    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass1234',
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            username='testsuperuser',
            email='testsuperuser@example.com',
            password='testpass1234',
        )
        self.assertEqual(admin_user.username, 'testsuperuser')
        self.assertEqual(admin_user.email, 'testsuperuser@example.com')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


class ExpenseModelTest(TestCase):
    def setUp(self):
        # Create a user and a category first
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpass'
        )
        self.category = Category.objects.create(
            user=self.user, 
            name='Groceries'
        )

    def test_expense_str(self):
        test_date = timezone.now()
        expense = Expense.objects.create(
            user=self.user,
            amount=100.0, 
            category=self.category, 
            date=test_date
        )
        expected_str = f"{expense.amount} - {self.category} on {test_date}"
        self.assertEqual(str(expense), expected_str)


class IncomeModelTest(TestCase):
    def setUp(self):
        # Create a user first
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpass'
        )

    def test_income_str(self):
        test_date = timezone.now()
        income = Income.objects.create(
            user=self.user,
            amount=5000.0, 
            date=test_date
        )
        expected_str = f"{income.amount} on {test_date}"
        self.assertEqual(str(income), expected_str)


class CategoryModelTest(TestCase):
    def setUp(self):
        # Create a user first
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpass'
        )

    def test_category_str(self):
        category = Category.objects.create(
            user=self.user,
            name='Groceries'
        )
        self.assertEqual(str(category), 'Groceries')


class BudgetModelTest(TestCase):
    def setUp(self):
        # Create a user and a category first
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpass'
        )
        self.category = Category.objects.create(
            user=self.user, 
            name='Groceries'
        )

    def test_budget_str(self):
        budget = Budget.objects.create(
            user=self.user,
            category=self.category, 
            amount=1000.0, 
            start_date=date(2023, 8, 1), 
            end_date=date(2023, 8, 31)
        )
        expected_str = f"{self.category} budget: {budget.amount}"
        self.assertEqual(str(budget), expected_str)


class SavingsGoalModelTest(TestCase):
    def setUp(self):
        # Create a user first
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpass'
        )

    def test_savings_goal_str(self):
        savings_goal = SavingsGoal.objects.create(
            user=self.user,
            goal_name='Vacation Fund',
            target_amount=5000.0,
            current_amount=1000.0,
            deadline=date(2023, 12, 31)
        )
        expected_str = f"{savings_goal.goal_name} - {savings_goal.current_amount}/{savings_goal.target_amount}"
        self.assertEqual(str(savings_goal), expected_str)
