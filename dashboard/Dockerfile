FROM python:3.14

# For real-time logging
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
COPY hardware_hound_logo_cropped.png .
COPY overclockers_logo.jpg .
COPY ebuyer_logo.png .
COPY awd_it_logo.png .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
