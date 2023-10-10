FROM python:3.10-slim

RUN mkdir /app

COPY requirements.txt /app/

WORKDIR /app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r /app/requirements.txt && rm -rf /root/.cache

COPY . /app/
EXPOSE 80

ENV STREAMLIT_SERVER_PORT=80
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
CMD ["streamlit", "run", "app.py"]
