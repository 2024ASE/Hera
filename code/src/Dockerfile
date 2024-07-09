FROM python:3.8

ARG MY_PARAM
ENV MY_PARAM=${MY_PARAM}

COPY /whl/* /whl/
RUN pip3 install /whl/*

ADD *.py /code/
COPY entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

ENTRYPOINT ["/code/entrypoint.sh"]


