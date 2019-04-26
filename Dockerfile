# Use an official Python runtime as a parent image
FROM python:3

ENV PYTHONUNBUFFERED 1

RUN mkdir /cr3

WORKDIR /cr3

ADD requirements.txt /cr3/

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

ADD . /cr3/

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
#CMD ["python", "manage.py", "runserver"]
