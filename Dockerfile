FROM python:3.8.1-slim

WORKDIR /
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

WORKDIR /workshop
COPY utils ./utils
COPY notify.py ./
COPY origin_unit_word.py ./
COPY word_count.py ./
COPY worker.py ./
COPY new_word.py ./
COPY start.sh ./


ENTRYPOINT [ "./start.sh" ]