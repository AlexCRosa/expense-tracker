from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from core.models import User, Category

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
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password123')
        self.category = Category.objects.create(user=self.user, name='Food', description='Groceries and dining')
        self.expense = Expense.objects.create(
            user=self.user,
            amount=100.50,
            category=self.category,
            description='Dinner at a restaurant',
            date=date(2024, 11, 25)
        )

    def test_expense_creation(self):
        self.assertEqual(self.expense.user, self.user)
        self.assertEqual(self.expense.amount, 100.50)
        self.assertEqual(self.expense.category, self.category)
        self.assertEqual(self.expense.description, 'Dinner at a restaurant')
        self.assertEqual(self.expense.date, date(2024, 11, 25))

    def test_expense_string_representation(self):
        self.assertEqual(
            str(self.expense),
            f"100.5 - {self.category} on {self.expense.date}"
        )

    def test_expense_list_view(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('core:expense_list'))

        self.assertContains(response, 'Dinner at a restaurant')
        self.assertContains(response, '100.50')
        self.assertEqual(response.status_code, 200)

    def test_expense_create_view(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('core:expense_create'), {
            'amount': 50.75,
            'category': self.category.id,
            'description': 'Groceries shopping',
            'date': '2024-11-26'
        })

        self.assertRedirects(response, reverse('core:expense_list'))
        self.assertEqual(Expense.objects.count(), 2)
        new_expense = Expense.objects.last()
        self.assertEqual(new_expense.description, 'Groceries shopping')

    def test_expense_update_view(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('core:expense_update', args=[self.expense.id]), {
            'amount': 120.00,
            'category': self.category.id,
            'description': 'Updated Dinner expense',
            'date': '2024-11-25'
        })

        self.assertRedirects(response, reverse('core:expense_list'))
        self.expense.refresh_from_db()
        self.assertEqual(self.expense.amount, 120.00)
        self.assertEqual(self.expense.description, 'Updated Dinner expense')

    def test_expense_delete_view(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('core:expense_delete', args=[self.expense.id]))

        self.assertRedirects(response, reverse('core:expense_list'))
        self.assertEqual(Expense.objects.count(), 0)

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
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password123')
        self.default_category1 = Category.objects.create(name='Default Category 1', user=None, description='')
        self.default_category2 = Category.objects.create(name='Default Category 2', user=None, description='')
        self.user_category = Category.objects.create(name='User Category', user=self.user, description='User-specific')

    def test_allow_duplicate_category_names_for_different_users(self):
        other_user = User.objects.create_user(username='otheruser', email='otheruser@example.com', password='password123')
        Category.objects.create(name='Duplicate Name', user=other_user)
        Category.objects.create(name='Duplicate Name', user=self.user)
        self.assertEqual(Category.objects.filter(name='Duplicate Name').count(), 2)

    def test_edit_default_category_creates_user_copy(self):
        self.client.login(username='testuser', password='password123')

        response = self.client.post(
            reverse('core:category_update', args=[self.default_category1.id]),
            {'name': self.default_category1.name, 'description': 'User edited description'}
        )

        self.assertRedirects(response, reverse('core:category_list'))
        user_specific_category = Category.objects.get(user=self.user, name=self.default_category1.name)
        self.assertEqual(user_specific_category.description, 'User edited description')

        default_category = Category.objects.get(pk=self.default_category1.id)
        self.assertEqual(default_category.description, '')

    def test_prevent_duplicate_category_names_for_user(self):
        self.client.login(username='testuser', password='password123')

        response = self.client.post(
            reverse('core:category_create'),
            {'name': self.user_category.name, 'description': 'Duplicate Name Attempt'}
        )

        self.assertContains(response, "You already have a category with this name.")

        self.assertEqual(
            Category.objects.filter(name=self.user_category.name, user=self.user).count(), 1 
        )

    def test_list_view_shows_correct_categories(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('core:category_list'))

        customized_category = Category.objects.create(
            user=self.user,
            name=self.default_category1.name,
            description="Customized Description"
        )
        response = self.client.get(reverse('core:category_list'))

        self.assertContains(response, customized_category.name)
        self.assertContains(response, customized_category.description)

    def test_delete_user_category(self):
        self.client.login(username='testuser', password='password123')

        response = self.client.post(reverse('core:category_delete', args=[self.user_category.id]))
        self.assertRedirects(response, reverse('core:category_list'))

        with self.assertRaises(Category.DoesNotExist):
            Category.objects.get(pk=self.user_category.id)


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
