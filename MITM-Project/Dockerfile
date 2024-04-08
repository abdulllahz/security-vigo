FROM ubuntu:22.04
RUN apt update
RUN apt install -y python3-psycopg2
RUN apt install -y mitmproxy
RUN apt install -y libyara-dev
RUN apt install -y python3-yara
#RUN pip install yara-python
COPY ./plugins /mitmproxy/plugins/
ENV MITMPROXY_ADDONS=/mitmproxy/plugins/core.py
WORKDIR /mitmproxy/plugins
CMD ["mitmdump", "-s", "core.py"]