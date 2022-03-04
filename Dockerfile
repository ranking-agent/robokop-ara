# leverage the renci python base image
FROM renciorg/renci-python-image:v0.0.1

RUN mkdir /robokop-ara
WORKDIR /robokop-ara

# set up requirements
COPY ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

# set up source
COPY . .

# let all files be accessible by non-root
RUN chmod 777 -R .

# switch to the new user created in the above image
USER nru

# set up entrypoint
CMD ["./main.sh"]
EXPOSE 7092
