from django.core.management.base import BaseCommand
from core.models import Category

class Command(BaseCommand):
    help = "Create default categories"

    def handle(self, *args, **kwargs):
        default_categories = [
            {"name": "Clothing", "description": "Clothing, footwear, and accessories"},
            {"name": "Entertainment", "description": "Movies, games, and recreational activities"},
            {"name": "Groceries", "description": "Groceries, food, and household supplies"},
            {"name": "Healthcare", "description": "Medical expenses and insurance"},
            {"name": "Housing", "description": "Rent, utilities, and mortgage payments"},
            {"name": "Miscellaneous", "description": "Other expenses not covered by other categories"},
            {"name": "Savings", "description": "Money set aside for future uses"},
            {"name": "Transportation", "description": "Public transport, fuel, and vehicle maintenance"},
            {"name": "Utilities", "description": "Electricity, water, and other utility bills"},
        ]

        for category_data in default_categories:
            category, created = Category.objects.get_or_create(
                name=category_data["name"],
                defaults={"description": category_data["description"], "user": None}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created default category: {category.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Category already exists: {category.name}"))
