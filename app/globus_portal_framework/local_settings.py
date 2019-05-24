# Create 'local_settings.py' and put your below values there to avoid
# accidentally committing them.
# Secret key can be generated with 'openssl rand -hex 32'
SECRET_KEY = '58b5c7558a2600fcc291a86bbae7e587c1a8d0bf446819d81f9e0ebafe184840'

# Get your keys at 'developers.globus.org'
SOCIAL_AUTH_GLOBUS_KEY = 'aed0df25-6de9-4b5f-a045-012888b6a5cd'
SOCIAL_AUTH_GLOBUS_SECRET = '9bRYHXNcaI0HR7dVOIylvBxTr+898hLK7OAg4nCHw0c='

ALLOWED_HOSTS = ['localhost', 'cbio.aurorabreastcancer.org']

# The search index in Globus Search
#SEARCH_INDEX = '11f4dbe5-1449-4d65-af83-72d322b117f3'   # production
#SEARCH_INDEX = 'dd2cdd6a-69d2-4b3d-aa99-c66fb995f96a'   # dev
SEARCH_INDEX = 'aurora'
ES_URL = '172.19.0.2'  # 'dbmi-appserver-prod-05.dbmi.pitt.edu'
ES_PORT = '9200'


SEARCH_RESULTS_PER_PAGE = 10
SEARCH_MAX_PAGES = 50
