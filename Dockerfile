FROM docker.io/python:3.9

COPY requirements.txt .
RUN pip install --user -r requirements.txt

COPY dictionary.txt .
COPY daily-words.txt .
ENV LOCALISATION en
COPY local/${LOCALISATION}.json localisation.json

COPY mastermind.py .
COPY bot.py .
ENV COMMAND_PREFIX %

ENTRYPOINT ["python", "-u", "./bot.py"]