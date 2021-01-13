FROM python:3

WORKDIR /src
ADD . /src

RUN pip install pytest retry requests pytest-mock numpy

ENV PYTHONPATH "${PYTHONPATH}:/src"
CMD [ "python", "/src/noclist/script.py" ]

