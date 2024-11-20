# Talon Expense Tracker

**It is a project created in the Python Project Development class at Wake Technical Community College.**

The **Expense Tracker** project is a web application designed to help users efficiently manage their personal finances. Built using Python and the Django framework, the application provides a simple and intuitive platform for users to log their income and expenses, categorize transactions, set budgets, and track savings goals.

## Features
- **User Registration and Authentication**:
  - Sign up, log in, and manage user accounts securely.
- **Expense and Income Logging**:
  - Log daily expenses and income with detailed descriptions and categorization.
- **Category Management**:
  - Create, edit, and organize categories for transactions.
- **Budget Tracking**:
  - Set monthly budgets for categories and monitor spending progress.
- **Savings Goals**:
  - Define savings goals, track progress, and stay motivated.

## Technologies Used
- **Frontend**: HTML and CSS (Django templates for dynamic content rendering)
- **Backend**: Python (Django Framework)
- **Database**: SQLite (integrated with Django for simplicity)

## Installation and Setup
Follow these steps to set up the project on your local machine:

### Prerequisites
- Python 3.x installed
- Pip (Python package manager) installed
- Virtual environment setup (recommended)

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/AlexCRosa/expense-tracker.git
   cd expense-tracker

2. **Create and activate a virtual environment**:
   ```bash
    python -m venv venv

    venv\Scripts\activate  # Windows
    source venv/bin/activate  # Linux / Mac

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt

4. **Set up the database: Run Django migrations to create the SQLite database**:
    ```bash
    python manage.py makemigrations
    python manage.py migrate

5. **Run the development server**:
    ```bash
    python manage.py runserver

6. **Access the application**: 
    - Open your browser and navigate to `http://127.0.0.1:8000/`.