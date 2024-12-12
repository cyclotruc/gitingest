FROM python:3.12

WORKDIR /app

# Create a non-root user
RUN useradd -m -u 1000 appuser

COPY src/ ./
COPY requirements.txt ./

RUN pip install -r requirements.txt

# Change ownership of the application files
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

CMD ["uvicorn", "main:app", "--reload"]
