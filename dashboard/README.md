# Dashboard Module

The dashboard module provides a Streamlit web application that serves as the main user interface for Hardware Hound. It manages core user flows including registration, credential authentication, sign-up email confirmation via Amazon SES, product tracking target configuration, and full item tracking visualizations.

---

## Project Structure

### Directories
This module consists of unified, flat dashboard scripts, configuration records, styling utilities, and target tests.

### Files
- [dashboard/requirements.txt](dashboard/requirements.txt): Contains target third-party dependencies (`streamlit`, `psycopg2-binary`, `bcrypt`, `boto3`, `python-dotenv`, `pytest-cov`, `bs4`, `regex`, `iso4217`) required to host the user application and execute the unit tests.
- [dashboard/app.py](dashboard/app.py): The main entry point of the application. Handles session initialization, routing rules for UI pages, and verification token parsing.
- [dashboard/auth.py](dashboard/auth.py): Implements security behaviors including new user signing-up registration, verification confirmation, and secure credential hashing utilizing bcrypt.
- [dashboard/database.py](dashboard/database.py): Houses the secure connection utility contexts using environment values or Secrets Manager data lookup alongside essential PostgreSQL query statements.
- [dashboard/form.py](dashboard/form.py): Constructs the visual interface enabling authenticated users to submit product URLs and target values, verifying URL formats before seeding items.
- [dashboard/tracked_products.py](dashboard/tracked_products.py): Implements the dashboard page which displays tracked item lists, metrics comparisons (Target Price vs Current/Original price), and untracking mechanics.
- [dashboard/ses_email.py](dashboard/ses_email.py): Coordinates integrations with Amazon SES to dispatch verification emails when user accounts are registered.
- [dashboard/style_components.py](dashboard/style_components.py): Contains visual component functions, trademark logos, grid spacing, and injected CSS styles.
- [dashboard/Dockerfile](dashboard/Dockerfile) and [dashboard/deploy_dashboard.sh](dashboard/deploy_dashboard.sh): Setup instructions and deployment commands to package the application container and push it to AWS ECR.
- [dashboard/conftest.py](dashboard/conftest.py): Hosts database transaction mocks and reusable pytest validation fixtures.
- [dashboard/test_database.py](dashboard/test_database.py), [dashboard/test_form.py](dashboard/test_form.py), [dashboard/test_login.py](dashboard/test_login.py), [dashboard/test_style_components.py](dashboard/test_style_components.py), [dashboard/test_tracked_products.py](dashboard/test_tracked_products.py): Comprehensive test files verifying database querying, login authentication, target input handling, and style structures.

---

## How to Run the Files

The Streamlit dashboard can be executed locally from the terminal. 

Ensure that you have set up your `.env` configuration file with your database credentials and AWS properties prior to launching the server.

To run the Streamlit local server, execute the application from the root workspace directory:

```bash
streamlit run dashboard/app.py
```