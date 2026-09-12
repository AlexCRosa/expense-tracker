from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse

from core.models import (
    Account,
    Budget,
    Category,
    SavingsGoal,
    Transaction,
    User,
)


class DashboardViewTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create(name="Checking-DashboardViewTests")
        # Create a test user and log them in
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="testpassword"
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="otheruser@example.com",
            password="otherpassword",
        )
        self.client.login(username="testuser", password="testpassword")

        # Create a category for expenses
        self.category = Category.objects.create(name="Groceries")

        # Create some expenses for the user
        Transaction.objects.create(
            type="expense",
            account=self.account,
            user=self.user,
            amount=999,
            category=self.category,
            date=datetime(2024, 11, 5),
        )
        Transaction.objects.create(
            type="expense",
            account=self.account,
            user=self.user,
            amount=100,
            category=self.category,
            date=datetime(2024, 11, 10),
        )
        Transaction.objects.create(
            type="expense",
            account=self.account,
            user=self.user,
            amount=200,
            category=self.category,
            date=datetime(2024, 11, 15),
        )
        Transaction.objects.create(
            type="expense",
            account=self.account,
            user=self.user,
            amount=50,
            category=self.category,
            date=datetime(2024, 11, 20),
        )

        # Create a budget for the user
        self.budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            amount=500,
            start_date="2024-11-01",
            end_date="2024-11-30",
        )

        # Create a savings goal for the user
        self.savings_goal = SavingsGoal.objects.create(
            user=self.user,
            goal_name="Vacation",
            target_amount=1000,
            current_amount=200,
            deadline=datetime(2024, 12, 31),
        )

        # Create an income entry for the user
        self.income1 = Transaction.objects.create(
            type="income",
            account=self.account,
            user=self.user,
            amount=100.50,
            description="Salary",
            date="2024-11-01",
        )
        self.income2 = Transaction.objects.create(
            type="income",
            account=self.account,
            user=self.user,
            amount=50.75,
            description="Freelance",
            date="2024-11-15",
        )

    def test_dashboard_access(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_last_three_expenses_displayed(self):
        response = self.client.get(reverse("core:dashboard") + "?month=11&year=2024")
        self.assertContains(response, "50.00")
        self.assertContains(response, "200.00")
        self.assertContains(response, "100.00")

    def test_budget_overview(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertContains(response, "Groceries")
        self.assertContains(response, "500.00")

    def test_savings_goals_display(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertContains(response, "Vacation")
        self.assertContains(response, "1,000.00")
        self.assertContains(response, "200.00")

    def test_income_summary(self):
        response = self.client.get(reverse("core:dashboard") + "?month=11&year=2024")
        self.assertContains(response, "Total Income This Month")
        self.assertContains(response, "151.25")

    def test_balance_section(self):
        response = self.client.get(reverse("core:dashboard") + "?month=11&year=2024")

        # Signed amounts, so the balance is simply their sum
        expected_balance = Transaction.objects.filter(
            date__month=11, date__year=2024
        ).aggregate(total=Sum("amount"))["total"]

        # Verify the balance calculation
        if expected_balance >= 0:
            self.assertContains(response, f"${expected_balance:,.2f}", html=True)
        else:
            self.assertContains(response, f"$-{abs(expected_balance):,.2f}", html=True)

    def test_filter_by_month_and_year(self):
        response = self.client.get(reverse("core:dashboard") + "?month=11&year=2024")
        self.assertContains(response, "50.00")
        self.assertContains(response, "200.00")
        self.assertContains(response, "100.00")

    def test_dashboard_unauthenticated_redirect(self):
        self.client.logout()
        response = self.client.get(reverse("core:dashboard"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next=/dashboard/")

    def test_second_user_sees_household_data(self):
        self.client.logout()
        self.client.login(username="otheruser", password="otherpassword")

        response = self.client.get(reverse("core:dashboard"))
        self.assertContains(response, "Vacation")
        self.assertContains(response, "Groceries")

    def test_no_data_message(self):
        response = self.client.get(
            reverse("core:dashboard"), {"person": self.other_user.pk}
        )
        self.assertContains(response, "No expenses added yet.")
        self.assertContains(response, "No savings goals yet.")
        self.assertContains(response, "No budgets set yet.")


class SavingsGoalContributionTest(TestCase):
    def setUp(self):
        self.account = Account.objects.create(
            name="Checking-SavingsGoalContributionTest"
        )
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="password123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="otheruser@example.com", password="password456"
        )
        self.savings = Category.objects.create(name="Savings")
        self.goal = SavingsGoal.objects.create(
            user=self.user,
            goal_name="Vacation",
            target_amount=1000,
            current_amount=100,
            created_at=date(2026, 1, 1),
            deadline=date(2026, 12, 31),
        )
        self.client.login(username="testuser", password="password123")

    def saved(self):
        return SavingsGoal.objects.with_saved_amount().get(pk=self.goal.pk).saved_amount

    def test_starting_save_counts_on_its_own(self):
        self.assertEqual(self.saved(), 100)

    def test_savings_inside_the_window_counts(self):
        Transaction.objects.create(
            type="savings",
            account=self.account,
            user=self.user,
            amount=250,
            category=self.savings,
            savings_goal=self.goal,
            date=date(2026, 6, 1),
        )
        self.assertEqual(self.saved(), 350)

    def test_savings_outside_the_window_does_not_count(self):
        Transaction.objects.create(
            type="savings",
            account=self.account,
            user=self.user,
            amount=250,
            category=self.savings,
            savings_goal=self.goal,
            date=date(2025, 12, 31),
        )
        self.assertEqual(self.saved(), 100)

    def test_savings_with_no_goal_does_not_count(self):
        Transaction.objects.create(
            type="savings",
            account=self.account,
            user=self.user,
            amount=250,
            category=self.savings,
            date=date(2026, 6, 1),
        )
        self.assertEqual(self.saved(), 100)

    def test_anyone_can_feed_a_goal(self):
        Transaction.objects.create(
            type="savings",
            account=self.account,
            user=self.other_user,
            amount=400,
            category=self.savings,
            savings_goal=self.goal,
            date=date(2026, 6, 1),
        )
        self.assertEqual(self.saved(), 500)

    def test_list_shows_starting_save_and_saved(self):
        Transaction.objects.create(
            type="savings",
            account=self.account,
            user=self.user,
            amount=250,
            category=self.savings,
            savings_goal=self.goal,
            date=date(2026, 6, 1),
        )
        response = self.client.get(reverse("core:savings_goal_list"))

        self.assertContains(response, "Starting Save")
        self.assertContains(response, "350")
        self.assertContains(response, "650")  # amount still to go

    def test_reclassified_contribution_stops_counting(self):
        contribution = Transaction.objects.create(
            type="savings",
            account=self.account,
            user=self.user,
            amount=250,
            category=self.savings,
            savings_goal=self.goal,
            date=date(2026, 6, 1),
        )
        self.assertEqual(self.saved(), 350)

        contribution.type = "income"
        contribution.save()

        self.assertEqual(self.saved(), 100)

    def test_goal_dropdown_hidden_until_a_goal_exists(self):
        response = self.client.get(reverse("core:expense_create"))
        self.assertContains(response, 'id="savings_goal_row"')

        SavingsGoal.objects.all().delete()
        response = self.client.get(reverse("core:expense_create"))
        self.assertNotContains(response, 'id="savings_goal_row"')


class AccountTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="password123"
        )
        self.client.login(username="testuser", password="password123")

    def test_create_account(self):
        response = self.client.post(
            reverse("core:account_create"), {"name": "BoA Checking"}
        )

        self.assertRedirects(response, reverse("core:account_list"))
        self.assertTrue(Account.objects.filter(name="BoA Checking").exists())

    def test_account_names_are_unique(self):
        Account.objects.create(name="BoA Checking")
        response = self.client.post(
            reverse("core:account_create"), {"name": "BoA Checking"}
        )

        self.assertContains(response, "Account with this Name already exists.")
        self.assertEqual(Account.objects.count(), 1)

    def test_list_and_delete_account(self):
        account = Account.objects.create(name="Capital One")
        response = self.client.get(reverse("core:account_list"))
        self.assertContains(response, "Capital One")

        response = self.client.post(reverse("core:account_delete", args=[account.pk]))
        self.assertRedirects(response, reverse("core:account_list"))
        self.assertFalse(Account.objects.filter(pk=account.pk).exists())


class ReviewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            first_name="Test",
            email="testuser@example.com",
            password="password123",
        )
        self.account = Account.objects.create(name="Checking")
        self.other_account = Account.objects.create(name="Credit Card")
        self.groceries = Category.objects.create(name="Groceries")
        self.dining = Category.objects.create(name="Dining")
        self.imported = Transaction.objects.create(
            user=self.user,
            account=self.account,
            type="expense",
            amount=45.67,
            category=self.groceries,
            description="COSTCO WHSE",
            date=date(2026, 9, 1),
        )
        self.client.login(username="testuser", password="password123")

    def test_unreviewed_shows_by_default(self):
        response = self.client.get(reverse("core:review_list"))

        self.assertContains(response, "COSTCO WHSE")
        self.assertContains(response, "1 transaction still to review.")

    def test_reviewed_hidden_unless_showing_all(self):
        self.imported.reviewed = True
        self.imported.save()

        response = self.client.get(reverse("core:review_list"))
        self.assertNotContains(response, "COSTCO WHSE")

        response = self.client.get(reverse("core:review_list"), {"show": "all"})
        self.assertContains(response, "COSTCO WHSE")

    def test_reviewing_records_who_and_when(self):
        response = self.client.post(
            reverse("core:review_update", args=[self.imported.pk]),
            {
                "account": self.account.pk,
                "type": "expense",
                "category": self.groceries.pk,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.imported.refresh_from_db()
        self.assertTrue(self.imported.reviewed)
        self.assertEqual(self.imported.reviewed_by, self.user)
        self.assertIsNotNone(self.imported.reviewed_at)

    def test_correcting_the_category_saves_and_reviews(self):
        self.client.post(
            reverse("core:review_update", args=[self.imported.pk]),
            {
                "account": self.other_account.pk,
                "type": "fee",
                "category": self.dining.pk,
            },
        )

        self.imported.refresh_from_db()
        self.assertEqual(self.imported.category, self.dining)
        self.assertEqual(self.imported.account, self.other_account)
        self.assertEqual(self.imported.type, "fee")
        self.assertTrue(self.imported.reviewed)

    def test_reviewing_leaves_the_amount_alone(self):
        self.client.post(
            reverse("core:review_update", args=[self.imported.pk]),
            {
                "account": self.account.pk,
                "type": "expense",
                "category": self.groceries.pk,
            },
        )

        self.imported.refresh_from_db()
        self.assertEqual(float(self.imported.amount), -45.67)

    def test_mark_all_reviewed(self):
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            type="expense",
            amount=10,
            category=self.dining,
            date=date(2026, 9, 2),
        )

        response = self.client.post(reverse("core:review_mark_all"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.filter(reviewed=False).count(), 0)
        self.assertEqual(Transaction.objects.filter(reviewed_by=self.user).count(), 2)

    def test_review_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("core:review_list"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next=/review/")


class DeleteGuardTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alex", first_name="Alex", email="a@b.c", password="pw123456"
        )
        self.other = User.objects.create_user(
            username="maria", first_name="Maria", email="m@b.c", password="pw123456"
        )
        self.account = Account.objects.create(name="Checking")
        self.category = Category.objects.create(name="Groceries")
        self.budget = Budget.objects.create(
            user=self.other,
            category=self.category,
            amount=300,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
        )
        self.transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            type="expense",
            amount=50,
            category=self.category,
            description="COSTCO",
            date=date(2026, 9, 5),
        )
        self.client.login(username="alex", password="pw123456")

    def test_category_in_use_cannot_be_deleted(self):
        response = self.client.post(
            reverse("core:category_delete", args=[self.category.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "in use and cannot be deleted")
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
        self.assertTrue(Budget.objects.filter(pk=self.budget.pk).exists())

    def test_category_page_lists_what_uses_it(self):
        response = self.client.get(
            reverse("core:category_delete", args=[self.category.pk])
        )

        self.assertContains(response, "COSTCO")
        self.assertContains(response, "Maria")

    def test_unused_category_still_deletes(self):
        spare = Category.objects.create(name="Spare")
        response = self.client.post(reverse("core:category_delete", args=[spare.pk]))

        self.assertRedirects(response, reverse("core:category_list"))
        self.assertFalse(Category.objects.filter(pk=spare.pk).exists())

    def test_account_with_transactions_cannot_be_deleted(self):
        response = self.client.post(
            reverse("core:account_delete", args=[self.account.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cannot be deleted")
        self.assertTrue(Account.objects.filter(pk=self.account.pk).exists())


class TypeCrossingTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alex", first_name="Alex", email="a@b.c", password="pw123456"
        )
        self.account = Account.objects.create(name="Checking")
        self.expense = Transaction.objects.create(
            user=self.user,
            account=self.account,
            type="expense",
            amount=50,
            date=date(2026, 9, 5),
        )
        self.income = Transaction.objects.create(
            user=self.user,
            account=self.account,
            type="income",
            amount=3000,
            date=date(2026, 9, 1),
        )
        self.client.login(username="alex", password="pw123456")

    def test_expense_cannot_be_edited_as_income(self):
        response = self.client.post(
            reverse("core:income_update", args=[self.expense.pk]),
            {"account": self.account.pk, "amount": 50, "date": "2026-09-05"},
        )

        self.assertEqual(response.status_code, 404)
        self.expense.refresh_from_db()
        self.assertEqual(self.expense.type, "expense")
        self.assertEqual(float(self.expense.amount), -50)

    def test_income_cannot_be_edited_as_expense(self):
        response = self.client.get(
            reverse("core:expense_update", args=[self.income.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_income_cannot_be_deleted_from_the_expense_page(self):
        response = self.client.post(
            reverse("core:expense_delete", args=[self.income.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Transaction.objects.filter(pk=self.income.pk).exists())


class DashboardInputTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alex", first_name="Alex", email="a@b.c", password="pw123456"
        )
        self.client.login(username="alex", password="pw123456")

    def test_out_of_range_month_and_year_fall_back(self):
        for query in [
            "month=13",
            "month=0",
            "year=0",
            "year=99999",
            "month=abc",
            "year=²",
        ]:
            response = self.client.get(f"{reverse('core:dashboard')}?{query}")
            self.assertEqual(response.status_code, 200, query)

    def test_malformed_person_falls_back(self):
        for url in [reverse("core:dashboard"), reverse("core:expense_list")]:
            response = self.client.get(url, {"person": "²"})
            self.assertEqual(response.status_code, 200, url)


class UserManagersTest(TestCase):
    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass1234",
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "testuser@example.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            username="testsuperuser",
            email="testsuperuser@example.com",
            password="testpass1234",
        )
        self.assertEqual(admin_user.username, "testsuperuser")
        self.assertEqual(admin_user.email, "testsuperuser@example.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


class ExpenseModelTest(TestCase):
    def setUp(self):
        self.account = Account.objects.create(name="Checking-ExpenseModelTest")
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="password123"
        )
        self.category = Category.objects.create(
            name="Food", description="Groceries and dining"
        )
        self.expense = Transaction.objects.create(
            type="expense",
            account=self.account,
            user=self.user,
            amount=100.50,
            category=self.category,
            description="Dinner at a restaurant",
            date=date(2024, 11, 25),
        )

    def test_expense_creation(self):
        self.assertEqual(self.expense.user, self.user)
        self.assertEqual(self.expense.amount, -100.50)
        self.assertEqual(self.expense.category, self.category)
        self.assertEqual(self.expense.description, "Dinner at a restaurant")
        self.assertEqual(self.expense.date, date(2024, 11, 25))

    def test_expense_string_representation(self):
        self.assertEqual(
            str(self.expense), f"-100.5 - {self.category} on {self.expense.date}"
        )

    def test_expense_list_view(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("core:expense_list"))

        self.assertContains(response, "Dinner at a restaurant")
        self.assertContains(response, "100.50")
        self.assertEqual(response.status_code, 200)

    def test_expense_create_view(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("core:expense_create"),
            {
                "account": self.account.id,
                "type": "expense",
                "amount": 50.75,
                "category": self.category.id,
                "description": "Groceries shopping",
                "date": "2024-11-26",
            },
        )

        self.assertRedirects(response, reverse("core:expense_list"))
        self.assertEqual(Transaction.objects.count(), 2)
        new_expense = Transaction.objects.last()
        self.assertEqual(new_expense.description, "Groceries shopping")

    def test_expense_update_view(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("core:expense_update", args=[self.expense.id]),
            {
                "account": self.account.id,
                "type": "expense",
                "amount": 120.00,
                "category": self.category.id,
                "description": "Updated Dinner expense",
                "date": "2024-11-25",
            },
        )

        self.assertRedirects(response, reverse("core:expense_list"))
        self.expense.refresh_from_db()
        self.assertEqual(self.expense.amount, -120.00)
        self.assertEqual(self.expense.description, "Updated Dinner expense")

    def test_expense_delete_view(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("core:expense_delete", args=[self.expense.id])
        )

        self.assertRedirects(response, reverse("core:expense_list"))
        self.assertEqual(Transaction.objects.count(), 0)


class IncomeModelTest(TestCase):
    def setUp(self):
        self.account = Account.objects.create(name="Checking-IncomeModelTest")
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="password123"
        )
        self.client.login(username="testuser", password="password123")
        self.income1 = Transaction.objects.create(
            type="income",
            account=self.account,
            user=self.user,
            amount=100.50,
            description="Salary",
            date="2024-11-01",
        )
        self.income2 = Transaction.objects.create(
            type="income",
            account=self.account,
            user=self.user,
            amount=50.75,
            description="Freelance",
            date="2024-11-15",
        )

    def test_income_list_view(self):
        response = self.client.get(reverse("core:income_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Salary")
        self.assertContains(response, "Freelance")
        self.assertTemplateUsed(response, "core/income_list.html")

    def test_income_create_view(self):
        response = self.client.post(
            reverse("core:income_create"),
            {
                "account": self.account.id,
                "amount": 200.00,
                "description": "Bonus",
                "date": "2024-11-20",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Transaction.objects.filter(description="Bonus").exists())

        income = Transaction.objects.get(description="Bonus")
        self.assertEqual(income.user, self.user)

    def test_income_update_view(self):
        response = self.client.post(
            reverse("core:income_update", kwargs={"pk": self.income1.pk}),
            {
                "account": self.account.id,
                "amount": 120.00,
                "description": "Updated Salary",
                "date": "2024-11-01",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.income1.refresh_from_db()
        self.assertEqual(self.income1.amount, 120.00)
        self.assertEqual(self.income1.description, "Updated Salary")

    def test_income_delete_view(self):
        response = self.client.post(
            reverse("core:income_delete", kwargs={"pk": self.income2.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Transaction.objects.filter(pk=self.income2.pk).exists())

    def test_income_list_shows_every_income(self):
        other_user = User.objects.create_user(
            username="otheruser", email="otheruser@example.com", password="password123"
        )
        Transaction.objects.create(
            type="income",
            account=self.account,
            user=other_user,
            amount=500.00,
            description="Other User Income",
            date="2024-11-10",
        )
        response = self.client.get(reverse("core:income_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Salary")
        self.assertContains(response, "Freelance")
        self.assertContains(response, "Other User Income")

    def test_filter_income_list_by_person(self):
        other_user = User.objects.create_user(
            username="otheruser", email="otheruser@example.com", password="password123"
        )
        Transaction.objects.create(
            type="income",
            account=self.account,
            user=other_user,
            amount=500.00,
            description="Other User Income",
            date="2024-11-10",
        )
        response = self.client.get(
            reverse("core:income_list"), {"person": other_user.pk}
        )

        self.assertContains(response, "Other User Income")
        self.assertNotContains(response, "Salary")


class CategoryModelTest(TestCase):
    def setUp(self):
        self.account = Account.objects.create(name="Checking-CategoryModelTest")
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="password123"
        )
        self.default_category1 = Category.objects.create(
            name="Default Category 1", description=""
        )
        self.default_category2 = Category.objects.create(
            name="Default Category 2", description=""
        )
        self.user_category = Category.objects.create(
            name="User Category", description="User-specific"
        )

    def test_category_names_are_unique(self):
        with self.assertRaises(IntegrityError):
            Category.objects.create(name=self.user_category.name)

    def test_edit_category_updates_it_for_everyone(self):
        self.client.login(username="testuser", password="password123")

        response = self.client.post(
            reverse("core:category_update", args=[self.default_category1.id]),
            {"name": self.default_category1.name, "description": "Edited description"},
        )

        self.assertRedirects(response, reverse("core:category_list"))
        self.default_category1.refresh_from_db()
        self.assertEqual(self.default_category1.description, "Edited description")
        self.assertEqual(Category.objects.filter(name="Default Category 1").count(), 1)

    def test_prevent_duplicate_category_names(self):
        self.client.login(username="testuser", password="password123")

        response = self.client.post(
            reverse("core:category_create"),
            {"name": self.user_category.name, "description": "Duplicate Name Attempt"},
        )

        self.assertContains(response, "Category with this Name already exists.")
        self.assertEqual(
            Category.objects.filter(name=self.user_category.name).count(), 1
        )

    def test_list_view_shows_every_category(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("core:category_list"))

        self.assertContains(response, self.default_category1.name)
        self.assertContains(response, self.default_category2.name)
        self.assertContains(response, self.user_category.name)
        self.assertContains(response, self.user_category.description)

    def test_delete_user_category(self):
        self.client.login(username="testuser", password="password123")

        response = self.client.post(
            reverse("core:category_delete", args=[self.user_category.id])
        )
        self.assertRedirects(response, reverse("core:category_list"))

        with self.assertRaises(Category.DoesNotExist):
            Category.objects.get(pk=self.user_category.id)


class BudgetModelTest(TestCase):
    def setUp(self):
        self.account = Account.objects.create(name="Checking-BudgetModelTest")
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="password123"
        )
        self.client.login(username="testuser", password="password123")

        self.other_user = User.objects.create_user(
            username="otheruser", email="otheruser@example.com", password="password456"
        )

        # Create categories for the users
        self.category1 = Category.objects.create(name="Entertainment")
        self.category2 = Category.objects.create(name="Groceries")

        # Create budgets for the first user
        self.budget1 = Budget.objects.create(
            user=self.user,
            category=self.category1,
            amount=150.00,
            start_date=date(2024, 11, 1),
            end_date=date(2024, 11, 30),
        )
        self.budget2 = Budget.objects.create(
            user=self.user,
            category=self.category2,
            amount=50.00,
            start_date=date(2024, 11, 1),
            end_date=date(2024, 11, 30),
        )

        # Add expenses for the first user
        Transaction.objects.create(
            type="expense",
            account=self.account,
            user=self.user,
            amount=70,
            category=self.category1,
            description="Movies",
            date=date(2024, 11, 5),
        )
        Transaction.objects.create(
            type="expense",
            account=self.account,
            user=self.user,
            amount=30,
            category=self.category1,
            description="Concert",
            date=date(2024, 11, 10),
        )
        Transaction.objects.create(
            type="expense",
            account=self.account,
            user=self.user,
            amount=50,
            category=self.category2,
            description="Groceries",
            date=date(2024, 11, 7),
        )

        # Create categories and expenses for the second user
        other_category = Category.objects.create(name="Other Entertainment")
        Transaction.objects.create(
            type="expense",
            account=self.account,
            user=self.other_user,
            amount=100,
            category=other_category,
            description="Other Expense",
            date=date(2024, 11, 5),
        )

    def test_budget_calculation(self):
        response = self.client.get(reverse("core:budget_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "150.00")  # Budget Defined for Entertainment
        self.assertContains(response, "100.00")  # Value Spent for Entertainment
        self.assertContains(response, "50.00")  # Budget Available for Entertainment
        self.assertContains(response, "50.00")  # Budget Defined for Groceries
        self.assertContains(response, "50.00")  # Value Spent for Groceries
        self.assertContains(response, "0.00")  # Budget Available for Groceries

    def test_budget_list_shows_every_budget_with_its_owner(self):
        self.client.login(username="otheruser", password="password456")
        response = self.client.get(reverse("core:budget_list"))

        self.assertContains(response, "Entertainment")
        self.assertContains(response, "Groceries")
        self.assertContains(response, "testuser")

    def test_filter_budget_list_by_person(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(
            reverse("core:budget_list"), {"person": self.other_user.pk}
        )

        self.assertNotContains(response, "Entertainment")

    def test_create_budget(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("core:budget_create"),
            {
                "category": self.category2.id,
                "amount": 200.00,
                "start_date": "2024-11-01",
                "end_date": "2024-11-30",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Budget.objects.filter(user=self.user, category=self.category2).exists()
        )

    def test_prevent_duplicate_budget_for_category(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("core:budget_create"),
            {
                "category": self.category1.id,
                "amount": 200.00,
                "start_date": "2024-11-01",
                "end_date": "2024-11-30",
            },
        )

        self.assertContains(response, "You already have a budget for this category.")

    def test_update_budget(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("core:budget_update", kwargs={"pk": self.budget1.id}),
            {
                "category": self.category1.id,
                "amount": 180.00,
                "start_date": "2024-11-01",
                "end_date": "2024-11-30",
            },
        )

        self.assertRedirects(response, reverse("core:budget_list"))
        self.budget1.refresh_from_db()
        self.assertEqual(self.budget1.amount, 180.00)

    def test_delete_budget(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("core:budget_delete", kwargs={"pk": self.budget1.id})
        )

        self.assertRedirects(response, reverse("core:budget_list"))
        self.assertFalse(Budget.objects.filter(id=self.budget1.id).exists())


class SavingsGoalModelTest(TestCase):
    def setUp(self):
        self.account = Account.objects.create(name="Checking-SavingsGoalModelTest")
        self.user = User.objects.create_user(
            username="testuser", password="password123", email="testuser@example.com"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="password456", email="otheruser@example.com"
        )

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

    def test_savings_goal_list_shows_every_goal(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("core:savings_goal_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.goal1.goal_name)
        self.assertContains(response, self.goal2.goal_name)
        self.assertContains(response, self.other_user_goal.goal_name)

    def test_filter_savings_goals_by_person(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(
            reverse("core:savings_goal_list"), {"person": self.other_user.pk}
        )

        self.assertContains(response, self.other_user_goal.goal_name)
        self.assertNotContains(response, self.goal1.goal_name)

    def test_edit_savings_goal(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("core:savings_goal_update", args=[self.goal1.id]),
            {
                "goal_name": "Updated Spring Break",
                "target_amount": 1500.00,
                "current_amount": 500.00,
                "deadline": date.today() + timedelta(days=40),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.goal1.refresh_from_db()
        self.assertEqual(self.goal1.goal_name, "Updated Spring Break")
        self.assertEqual(self.goal1.target_amount, 1500.00)
        self.assertEqual(self.goal1.current_amount, 500.00)

    def test_delete_savings_goal(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("core:savings_goal_delete", args=[self.goal1.id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(SavingsGoal.objects.filter(id=self.goal1.id).exists())

    def test_deadline_display(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("core:savings_goal_list"))

        self.assertContains(response, "30 days to go")
        self.assertContains(response, "60 days to go")
