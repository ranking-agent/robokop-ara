FROM python:3.9.1-buster


# set up requirements
ADD ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

# create a new user and use it.
RUN useradd -M -u 1001 nonrootuser
USER nonrootuser
# set up source
ADD ./app ./app
ADD ./main.sh ./main.sh

# set up entrypoint
CMD ["./main.sh"]
ARG PORT=8080
EXPOSE $PORT