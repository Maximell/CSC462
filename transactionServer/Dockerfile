FROM python:2.7

ADD . /runcode
WORKDIR ./runcode
RUN pip install -r requirements.txt
CMD ["python" , "./runcode/transactionServer.py" , "seng462"]
EXPOSE 4442
