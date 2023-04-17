FROM python:3.9-slim-buster
WORKDIR /app
COPY api.py api.py
RUN pip3 install flask
COPY . .
CMD ["python3", "api.py"]