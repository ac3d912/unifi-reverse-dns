
FROM python:3.8

WORKDIR /usr/src/app
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Install this handy login/logout script (no setup.py, so just move it around)
RUN git clone https://github.com/frehov/Unifi-Python-API.git unifi-python-api
RUN mv unifi-python-api/ubiquiti .
RUN rm -rf unifi-python-api

ENV SITE=default
#ENV USERNAME=
#ENV PASSWORD=
ENV BASE_URL=https://unifi:8443
ENV VERIFY_SSL=True

COPY main.py ./

CMD [ "python", "-u", "./main.py" ]
