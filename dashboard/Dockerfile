FROM python:3.14

# For real-time logging
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY dashboard/requirements.txt .
COPY dashboard/hardware_hound_logo_cropped.png .
COPY dashboard/overclockers_logo.jpg .
COPY dashboard/ebuyer_logo.png .
COPY dashboard/awd_it_logo.png .

RUN pip install --no-cache-dir -r requirements.txt

COPY dashboard/form.py dashboard/auth.py dashboard/ses_email.py dashboard/style_components.py dashboard/app.py dashboard/database.py dashboard/discord_link.py dashboard/tracked_products.py ./
COPY dashboard/.streamlit/config.toml .streamlit/config.toml

# Scrapers and cleaner (dynamically loaded by form.py at runtime)
COPY full_scraping/awd-it/awd_it_full_scraper.py /full_scraping/awd-it/
COPY full_scraping/ebuyer/ebuyer_full_scraper.py /full_scraping/ebuyer/
COPY full_scraping/overclockers/overclockers_full_scraper.py /full_scraping/overclockers/
COPY cleaning/cleaning.py /cleaning/

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
