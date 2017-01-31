FROM python:3.4-apline

ADD . /runcode
WORKDIR /runcode 
RUN pip install -r requirements.txt 
CMD ["python" , "testDriver.py" , "localhost" , "4442", "2userWorkLoad.txt"]
