FROM python:3.14

# For real-time logging
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cleaning/ cleaning/
COPY full_scraping/ full_scraping/
COPY form.py auth.py ses_email.py style_components.py app.py database.py discord_link.py tracked_products.py .
COPY .streamlit/config.toml .streamlit/config.toml

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
