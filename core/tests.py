from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from core.models import User, Expense, Income, Category, Budget, SavingsGoal


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
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password123')
        self.client.login(username='testuser', password='password123')
        self.income1 = Income.objects.create(user=self.user, amount=100.50, description="Salary", date="2024-11-01")
        self.income2 = Income.objects.create(user=self.user, amount=50.75, description="Freelance", date="2024-11-15")

    def test_income_list_view(self):
        response = self.client.get(reverse('core:income_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Salary")
        self.assertContains(response, "Freelance")
        self.assertTemplateUsed(response, 'core/income_list.html')

    def test_income_create_view(self):
        response = self.client.post(reverse('core:income_create'), {
            'amount': 200.00,
            'description': 'Bonus',
            'date': '2024-11-20',
        })

        self.assertEqual(response.status_code, 302) 
        self.assertTrue(Income.objects.filter(description='Bonus').exists())

        income = Income.objects.get(description='Bonus')
        self.assertEqual(income.user, self.user)

    def test_income_update_view(self):
        response = self.client.post(reverse('core:income_update', kwargs={'pk': self.income1.pk}), {
            'amount': 120.00,
            'description': 'Updated Salary',
            'date': '2024-11-01',
        })

        self.assertEqual(response.status_code, 302)
        self.income1.refresh_from_db()
        self.assertEqual(self.income1.amount, 120.00)
        self.assertEqual(self.income1.description, 'Updated Salary')

    def test_income_delete_view(self):
        response = self.client.post(reverse('core:income_delete', kwargs={'pk': self.income2.pk}))

        self.assertEqual(response.status_code, 302) 
        self.assertFalse(Income.objects.filter(pk=self.income2.pk).exists())

    def test_income_list_shows_only_user_incomes(self):
        other_user = User.objects.create_user(username='otheruser', email='otheruser@example.com', password='password123')
        Income.objects.create(user=other_user, amount=500.00, description="Other User Income", date="2024-11-10")
        response = self.client.get(reverse('core:income_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Salary")
        self.assertContains(response, "Freelance")
        self.assertNotContains(response, "Other User Income")


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
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password123')
        self.client.login(username='testuser', password='password123') 

        self.other_user = User.objects.create_user(username='otheruser', email='otheruser@example.com', password='password456')

        # Create categories for the users
        self.category1 = Category.objects.create(user=self.user, name='Entertainment')
        self.category2 = Category.objects.create(user=self.user, name='Groceries')

        # Create budgets for the first user
        self.budget1 = Budget.objects.create(
            user=self.user,
            category=self.category1,
            amount=150.00,
            start_date=date(2024, 11, 1),
            end_date=date(2024, 11, 30)
        )
        self.budget2 = Budget.objects.create(
            user=self.user,
            category=self.category2,
            amount=50.00,
            start_date=date(2024, 11, 1),
            end_date=date(2024, 11, 30)
        )

        # Add expenses for the first user
        Expense.objects.create(user=self.user, amount=70, category=self.category1, description="Movies", date=date(2024, 11, 5))
        Expense.objects.create(user=self.user, amount=30, category=self.category1, description="Concert", date=date(2024, 11, 10))
        Expense.objects.create(user=self.user, amount=50, category=self.category2, description="Groceries", date=date(2024, 11, 7))

        # Create categories and expenses for the second user
        other_category = Category.objects.create(user=self.other_user, name='Other Entertainment')
        Expense.objects.create(user=self.other_user, amount=100, category=other_category, description="Other Expense", date=date(2024, 11, 5))

    def test_budget_calculation(self):
        response = self.client.get(reverse('core:budget_list')) 

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "150.00")  # Budget Defined for Entertainment
        self.assertContains(response, "100.00")  # Value Spent for Entertainment
        self.assertContains(response, "50.00")   # Budget Available for Entertainment
        self.assertContains(response, "50.00")   # Budget Defined for Groceries
        self.assertContains(response, "50.00")   # Value Spent for Groceries
        self.assertContains(response, "0.00")    # Budget Available for Groceries

    def test_budget_visible_to_owner_only(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('core:budget_list'))

        self.assertContains(response, 'Entertainment')
        self.assertContains(response, 'Groceries')

        self.client.logout()

        self.client.login(username='otheruser', password='password456')
        response = self.client.get(reverse('core:budget_list'))

        self.assertNotContains(response, 'Entertainment')
        self.assertNotContains(response, 'Groceries')

    def test_create_budget(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('core:budget_create'), {
            'category': self.category2.id,
            'amount': 200.00,
            'start_date': '2024-11-01',
            'end_date': '2024-11-30'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Budget.objects.filter(user=self.user, category=self.category2).exists())

    def test_prevent_duplicate_budget_for_category(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('core:budget_create'), {
            'category': self.category1.id,
            'amount': 200.00,
            'start_date': '2024-11-01',
            'end_date': '2024-11-30'
        })

        self.assertContains(response, "You already have a budget for this category.")

    def test_update_budget(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('core:budget_update', kwargs={'pk': self.budget1.id}), {
            'category': self.category1.id,
            'amount': 180.00,
            'start_date': '2024-11-01',
            'end_date': '2024-11-30'
        })

        self.assertRedirects(response, reverse('core:budget_list'))
        self.budget1.refresh_from_db()
        self.assertEqual(self.budget1.amount, 180.00)

    def test_delete_budget(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('core:budget_delete', kwargs={'pk': self.budget1.id}))

        self.assertRedirects(response, reverse('core:budget_list'))
        self.assertFalse(Budget.objects.filter(id=self.budget1.id).exists())


class SavingsGoalModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123', email='testuser@example.com')
        self.other_user = User.objects.create_user(username='otheruser', password='password456', email='otheruser@example.com')

        self.goal1 = SavingsGoal.objects.create(
            user=self.user,
            goal_name="Spring Break Travel",
            target_amount=1200.00,
            current_amount=300.00,
            deadline=date.today() + timedelta(days=30),
        )

        self.goal2 = SavingsGoal.objects.create(
            user=self.user,
            goal_name="Christmas Dinner",
            target_amount=200.00,
            current_amount=100.00,
            deadline=date.today() + timedelta(days=60),
        )

        self.other_user_goal = SavingsGoal.objects.create(
            user=self.other_user,
            goal_name="Other User Goal",
            target_amount=100.00,
            current_amount=50.00,
            deadline=date.today() + timedelta(days=10),
        )

    def test_savings_goal_creation(self):
        goal = SavingsGoal.objects.create(
            user=self.user,
            goal_name="New Savings Goal",
            target_amount=500.00,
            current_amount=0.00,
            deadline=date.today() + timedelta(days=90),
        )

        self.assertEqual(goal.user, self.user)
        self.assertEqual(goal.goal_name, "New Savings Goal")
        self.assertEqual(goal.target_amount, 500.00)
        self.assertEqual(goal.current_amount, 0.00)

    def test_amount_to_goal_calculation(self):
        self.assertEqual(self.goal1.target_amount - self.goal1.current_amount, 900.00)
        self.assertEqual(self.goal2.target_amount - self.goal2.current_amount, 100.00)

    def test_filter_savings_goals_by_user(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('core:savings_goal_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.goal1.goal_name)
        self.assertContains(response, self.goal2.goal_name)
        self.assertNotContains(response, self.other_user_goal.goal_name)

    def test_edit_savings_goal(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('core:savings_goal_update', args=[self.goal1.id]), {
            'goal_name': 'Updated Spring Break',
            'target_amount': 1500.00,
            'current_amount': 500.00,
            'deadline': date.today() + timedelta(days=40),
        })

        self.assertEqual(response.status_code, 302)
        self.goal1.refresh_from_db()
        self.assertEqual(self.goal1.goal_name, 'Updated Spring Break')
        self.assertEqual(self.goal1.target_amount, 1500.00)
        self.assertEqual(self.goal1.current_amount, 500.00)

    def test_delete_savings_goal(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('core:savings_goal_delete', args=[self.goal1.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(SavingsGoal.objects.filter(id=self.goal1.id).exists())

    def test_deadline_display(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('core:savings_goal_list'))

        self.assertContains(response, "30 days to go")
        self.assertContains(response, "60 days to go")
        