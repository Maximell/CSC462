FROM python:3

ADD . /runcode
WORKDIR /runcode 
RUN pip install -r requirements.txt 
CMD ["python" , "testDriver.py" , "https://172.17.0.2:4442", "2userWorkLoad.txt"]
