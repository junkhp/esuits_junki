FROM python:3.7
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN mkdir /app
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ./entrypoint.sh /app/entrypoint.sh
COPY . /app/
ENTRYPOINT [ "/app/entrypoint.sh" ]