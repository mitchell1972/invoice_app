from setuptools import setup, find_packages

setup(
    name="invoice_app",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "pydantic==2.4.2",
        "pydantic-settings==2.1.0",
        "sqlalchemy==2.0.23",
        "psycopg2-binary==2.9.9",
        "python-dotenv==1.0.0",
        "alembic==1.12.1",
        "email-validator==2.1.0",
    ],
) 