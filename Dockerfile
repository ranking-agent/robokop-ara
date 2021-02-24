FROM python:3.9.1-buster

# set up requirements
ADD ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

# set up source
ADD ./app ./app
ADD ./main.sh ./main.sh
ADD ./.env ./.env

ARG PORT=8080
EXPOSE $PORT

# set up entrypoint
ENTRYPOINT ["bash", "main.sh"]
