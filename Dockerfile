FROM python:3.11-bullseye

RUN mkdir /ai
WORKDIR /ai

COPY . ./

RUN pip install -r requirements.txt
ENTRYPOINT ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--timeout-keep-alive", "600"]
