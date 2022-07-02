# syntax=docker/dockerfile:1
FROM python:3.9-buster AS python
WORKDIR /bots
COPY . .

VOLUME /bots

RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y nodejs npm
RUN npm install -g pm2@latest

CMD ["uvicorn", "web.api:app", "--host", "0.0.0.0", "--port", "80"]
