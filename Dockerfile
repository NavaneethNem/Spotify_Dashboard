FROM python:3.14
#FROM starts a container with an environment that already has Python 3.12 installed

WORKDIR /app
#WORKDIR sets the current working directory to a new folder 'app'

COPY requirements.txt .
#The . means the current working directory inside the image, which is now /app

COPY main.py .

RUN pip install -r requirements.txt
#To install the dependencies

CMD ["python","main.py"]