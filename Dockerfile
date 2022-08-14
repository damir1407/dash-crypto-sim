FROM python:3.9
COPY requirements.txt /tmp/
COPY ./app /app
WORKDIR "/app"
RUN pip3 install -r /tmp/requirements.txt
RUN pip3 install dash --upgrade
ENTRYPOINT [ "python3" ]
CMD [ "app.py" ]
