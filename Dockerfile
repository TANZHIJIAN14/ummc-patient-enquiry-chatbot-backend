FROM python:3.9-slim

# Set the working directory
WORKDIR /demo-llm

# Install system dependencies (if necessary)
RUN apt-get update && apt-get install -y --no-install-recommends curl

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false && poetry install --no-root

# Copy the rest of the application code
COPY . .