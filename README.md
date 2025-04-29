# ScienceBridge

An agent that accelerates scientific research by autonomously navigating across provided science datasets, generating hypotheses, and validating them through code

# Generate a new migration with a descriptive name:

alembic revision --autogenerate -m "add_usage_table"

# To check the current state of your database

alembic current

# Generate a new migration

alembic revision --autogenerate -m "add_usage_table"

# Apply the migration to update the database

alembic upgrade head

# If you need to revert the migration

alembic downgrade -1

# Check migration history

alembic history
