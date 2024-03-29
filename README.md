# Django, uWSGI and Nginx in a container, using Supervisord

This Dockerfile shows you *how* to build a Docker container with a fairly standard
and speedy setup for Django with uWSGI and Nginx.

uWSGI from a number of benchmarks has shown to be the fastest server 
for python applications and allows lots of flexibility. But note that we have
not done any form of optimalization on this package. Modify it to your needs.

Nginx has become the standard for serving up web applications and has the 
additional benefit that it can talk to uWSGI using the uWSGI protocol, further
eliminating overhead. 

Most of this setup comes from the excellent tutorial on 
https://uwsgi.readthedocs.org/en/latest/tutorials/Django_and_nginx.html

The best way to use this repository is as an example. Clone the repository to 
a location of your liking, and start adding your files / change the configuration 
as needed. Once you're really into making your project you'll notice you've 
touched most files here.

### Build and run
#### Build with python3
* `docker build -t ddp .`
* docker run -d -p 4435:4435 --net=elasticsearch_es01 --name ddp ddp
## Elasticsearch
Use docker-compose file to build a es-based container
/elasticsearch/docker-compose.yml


### Static files
You must do the following:

-	Enabled DocumentRoot "/var/www/html" in the ssl.conf file

-	Copied static files to the following directory,  /var/www/html/static
    	    drwxr-xr-x 4 root root  27 Jun  8 13:39 bootstrap
	    drwxr-xr-x 2 root root 253 Jun  8 13:32 css
	    drwxr-xr-x 2 root root 212 Jun  8 13:52 img
            drwxr-xr-x 2 root root 325 Jun  8 13:32 js

