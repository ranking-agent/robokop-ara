# leverage the renci python base image
FROM renciorg/renci-python-image:v0.0.1

# switch to the new user created in the above image
USER nru

# set up requirements
COPY ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

# set up source
COPY . .

# set up entrypoint
CMD ["./main.sh"]
EXPOSE 7092
