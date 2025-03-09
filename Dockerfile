FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and dependencies
RUN playwright install
RUN playwright install-deps

COPY main.py .

RUN mkdir pdfs

EXPOSE 8000

CMD ["python", "main.py"] 