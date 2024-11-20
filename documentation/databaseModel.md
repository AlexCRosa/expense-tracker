# Data Model Outline

## Entities and Relationships

### 1. User
This entity represents the users of the application.
- **Attributes**:
  - `id` (Primary Key): Unique identifier for each user.
  - `first_name`: The user's first name
  - `last_name`: The user's last_name
  - `username`: The user's chosen username.
  - `email`: The user's email address.
  - `password`: The user's hashed password for authentication.
  - `date_joined`: The date when the user created their account.

- **Relationships**:
  - A User can have multiple `Expense` records.
  - A User can have multiple `Income` records.
  - A User can set multiple `Category` and `Budget` records.
  - A User can have multiple `SavingsGoal` records.

### 2. Expense
This entity records individual expenses logged by users.
- **Attributes**:
  - `id` (Primary Key): Unique identifier for each expense.
  - `user` (Foreign Key): The user who logged the expense.
  - `amount`: The amount of the expense.
  - `category` (Foreign Key): The category to which the expense belongs.
  - `description`: Optional description of the expense.
  - `date`: The date and time when the expense was logged.

- **Relationships**:
  - An Expense belongs to one `User`.
  - An Expense is associated with one `Category`.

### 3. Income
This entity records income entries for users.
- **Attributes**:
  - `id` (Primary Key): Unique identifier for each income entry.
  - `user` (Foreign Key): The user who logged the income.
  - `amount`: The amount of income.
  - `description`: Optional description of the income.
  - `date`: The date and time when the income was logged.

- **Relationships**:
  - An Income entry belongs to one `User`.

### 4. Category
This entity represents categories that users can create for organizing their expenses.
- **Attributes**:
  - `id` (Primary Key): Unique identifier for each category.
  - `user` (Foreign Key): The user who created the category.
  - `name`: The name of the category (e.g., "Groceries", "Rent").
  - `description`: Optional description of the category.

- **Relationships**:
  - A Category belongs to one `User`.
  - A Category can have multiple `Expense` records associated with it.

### 5. Budget
This entity represents budget limits set by users for specific categories.
- **Attributes**:
  - `id` (Primary Key): Unique identifier for each budget.
  - `user` (Foreign Key): The user who set the budget.
  - `category` (Foreign Key): The category for which the budget is set.
  - `amount`: The budget limit amount.
  - `start_date`: The start date of the budget period.
  - `end_date`: The end date of the budget period.

- **Relationships**:
  - A Budget belongs to one `User`.
  - A Budget is associated with one `Category`.

### 6. SavingsGoal
This entity tracks the savings goals set by users.
- **Attributes**:
  - `id` (Primary Key): Unique identifier for each savings goal.
  - `user` (Foreign Key): The user who set the savings goal.
  - `goal_name`: The name or description of the savings goal (e.g., "Vacation Fund").
  - `target_amount`: The amount the user aims to save.
  - `current_amount`: The amount currently saved.
  - `deadline`: The target date for achieving the goal.

- **Relationships**:
  - A SavingsGoal belongs to one `User`.
