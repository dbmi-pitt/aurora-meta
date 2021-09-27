from __future__ import division

from datetime import timedelta, datetime
import json
import time
import logging
from importlib import import_module
from urllib.parse import quote_plus, unquote
import globus_sdk
import http.client
import ssl

from globus_portal_framework import settings as g_settings
from globus_portal_framework.search import settings
from globus_portal_framework.transfer import settings as t_settings
from globus_portal_framework.utils import load_globus_client
from elasticsearch import Elasticsearch

log = logging.getLogger(__name__)
access_log = logging.getLogger('access_logger')

def load_json_file(filename):
    with open(filename) as f:
        raw_data = f.read()
        return json.loads(raw_data)


SEARCH_SCHEMA = load_json_file(settings.SEARCH_SCHEMA)

def post_search(index, query, filters, user=None, page=1, advanced=False):
    print("post search")
    print(filters)

    if query == '*' and len(filters) > 0:
        query = ""

    if advanced:
        adv_query = reformat_filters(filters)
        if adv_query and len(adv_query) > 0:
            if len(query) > 0:
                query += " AND " + adv_query
            else:
                query = adv_query
        gfilters = ""

    # log all queries to access log
    access_log.info('User: {} - Query: {}'.format(user, query))        

    return search_es(query)


def search_es(querystr):
    result = []
    es_url = ""

    if g_settings.DEBUG:
        es_url = 'localhost'
    else:
        es_url = settings.ES_URL

    print('ES Host: {}:{}'.format(es_url, settings.ES_PORT))
    
    try:
        es = Elasticsearch([{'host': es_url, 'port': settings.ES_PORT}])
    except Exception as e:
        print('There is a problem with the ES instance, trying the localhost!!')
        es = Elasticsearch([{'host': 'localhost', 'port': settings.ES_PORT}])

    tokens = querystr.split(" ")

    if len(tokens) == 1 and querystr != "*":
        if querystr.find("-") > -1:
            querystr = '\"' + str(querystr) + '\"'

    #print(querystr)

    # form basic query body
    body = { "from": 0, "size": 1000,
        "size": 1000,
        "query": {
           "query_string": {
                "query": querystr,
                "analyze_wildcard": True,
                "default_field": "*"
           }
        }        
#        , 'aggs': {'anatomic_site': {'terms': {'field': 'anatomic_site.keyword'}}}
#        "aggs": {
#            "anatomic_site": {
#                "terms": {"field":"anatomic_site.keyword"}
#            }
#        }
    }

    # check the SEARCH_SCHEMA['facets'] for 'active' facets/aggregates
    a = {}
    a['aggs'] = {}
    for f in SEARCH_SCHEMA['facets']:
        if f["active"] == 'true':
            ae = {}       
            t = {}
            x = f["field_name"] + ".keyword"
            t['terms'] = {"field": x }
            ae[f['field_name']] = t
            a['aggs'].update(ae)
    print(SEARCH_SCHEMA['facets'])
    body.update(a)   # update the query body with aggregates
    #print(body)

    try:
        #q = "content." + q
        #print(q)
        res = es.search(index=settings.SEARCH_INDEX, body=body)
#        print("ES: %d documents found" % res['hits']['total'])
        #print(res['hits']['hits'])
        #print(res)
        gfilters = {}
        results = process_search_data(res['hits']['hits'])
        facets = get_facets(res['aggregations'], SEARCH_SCHEMA, gfilters)

        # TEMP SOLUTION!!!!
        images = ""
        try:
            images = get_imagemap()
            print(images)
        except Exception as e:
            print("Can't get the image map!!!!")
        
        #print(results)
        # TEST FOR REPORT SEARCH
#        reports = search_es_reports(querystr)
        #print(facets)        

    except Exception as e:
        print('Unable to get results from data')
        print(e)
        raise e
    #for doc in res['hits']['hits']:
    #    print("%s) %s" % (doc['_id'], doc['_source']['content']))
    return {'search_results': results, 
            'result_total': res['hits']['total'], 
            'facets':facets,
            'query':querystr,
            'images':images,
            'filters': pretty_filters(querystr) #pretty_filters(fmt_filters)
#            'report_results': reports['report_results'],
 #           'report_total': reports['report_total']
            }

# convert field names into pretty names from the facet definitions
def pretty_filters(qstr):

    filter_toks = qstr.split()
    position = 0
    for t in filter_toks:
        expr = t.split(":")
        if len(expr) > 1:
            for f in SEARCH_SCHEMA['facets']:
                if expr[0] == f["field_name"]:
                    filter_toks[position] = f["name"] + ":" + expr[1]
                    break
        position = position + 1
    return ' '.join(filter_toks)


# this reformats the filters to a format that is used by Elasticsearch 
# https://www.elastic.co/guide/en/elasticsearch/reference/6.4/query-dsl-query-string-query.html#query-string-syntax
def reformat_filters(filters):
    query_list = []
    keys = filters.keys()
    adv_query = ""

    # loop through all the key values and get respective values
    for k in list(keys):
        values = filters[k]
        if len(values) > 1:
            multi_val = ""            
            for v in values:
                multi_val += '"' + str(v) + '" OR '
            #print(multi_val)
            query_list.append(str(k) + ":(" + str(multi_val[0:-4]) + ")")

        else:
            s = str(k) + ':"' + values[0] + '"'
            query_list.append(s)

    #print(query_list)
    if len(query_list) > 0:
        for q in query_list:
            adv_query += q + ' AND '

        adv_query = adv_query[0:-5]  # truncate the extra AND

    return adv_query

def default_search_mapper(gmeta_result, schema):
    """This mapper takes the given schema and maps all fields within the
    gmeta entry against it. Any non-matching results simply won't
    show up in the result. This approach avoids a bunch of empty fields being
    displayed when rendered in the templates.
    :param entry:
        entry = {
            'foo': 'bar'
            'car': 'zar'
        }
    :param schema:
        schema = {
            'foo': {'field_title': 'Foo'}
        }
    :returns template_results:
    Will return:
        {
        'foo': {'field_title': 'Foo', 'value': 'bar'}
        }
    """
    #print(gmeta_result)
    entry = gmeta_result[0][settings.SEARCH_ENTRY_FIELD_PATH]
    fields = {k: {
                       'field_title': schema[k].get('field_title', k),
                       'data': v
                  } for k, v in entry.items() if schema.get(k)}
    if not fields.get('title'):
        fields['title'] = entry.get(settings.SEARCH_ENTRY_TITLE)
        if isinstance(fields['title'], list):
            fields['title'] = fields['title'].pop(0)
    return fields


def default_service_mapper(gmeta_result, entry_service_vars):
    """
    Like the default search mapper, but looks for ENTRY_SERVICE_VARS for
    each search result. This function should only be updated if the variables
    are scattered in the entry and custom logic is the only way to retrieve
    them. Otherwise, update ENTRY_SERVICE_VARS in settings.py
    :param gmeta_result: The current gmeta_result
    :param variable_map: Typically ENTRY_SERVICE_VARS stored in settings
    :return: A dict matching the keys in variable_map, with values of vars
    found in the gmeta_result. If the key doesn't exist, the variable is set
    to None
    """
    entry = gmeta_result[0][settings.SEARCH_ENTRY_FIELD_PATH]
    return {
        key: entry.get(val) for key, val in entry_service_vars.items()
    }


def get_subject(subject, user=None):
    """Get a subject and run the result through the SEARCH_MAPPER defined
    in settings.py. If no subject exists, return context with the 'subject'
    and an 'error' message."""
    client = load_search_client(user)
    try:
        result = client.get_subject(settings.SEARCH_INDEX, unquote(subject))
        return process_search_data([result.data])[0]
    except globus_sdk.exc.SearchAPIError:
        return {'subject': subject, 'error': 'No data was found for subject'}


def load_search_client(user=None):
    """Load a globus_sdk.SearchClient, with a token authorizer if the user is
    logged in or a generic one otherwise."""
    return load_globus_client(user, globus_sdk.SearchClient,
                              'search.api.globus.org')


def process_search_data(results):
    """
    Process results in a general search result, running the mapping function
    for each result and preparing other general data for being shown in
    templates (such as quoting the subject and including the index).
    :param results: List of GMeta results, which would be the r.data['gmeta']
    in from a simple query to Globus Search. See here:
    https://docs.globus.org/api/search/schemas/GMetaResult/
    :return: A list of search results:


    """
    field_mod_name, field_func_name = settings.SEARCH_MAPPER
    field_mod = import_module(field_mod_name)
    field_mapper = getattr(field_mod, field_func_name, default_search_mapper)
    service_mod_name, service_func_name = t_settings.ENTRY_SERVICE_VARS_MAPPER
    service_mod = import_module(service_mod_name)
    service_mapper = getattr(service_mod, service_func_name,
                             default_service_mapper)
    structured_results = []
    for entry in results:
        #print(entry)
        structured_results.append({
            #'subject': quote_plus(entry['_source']['REDCAP_ID']),     #['subject']),
            'subject': entry['_id'],     #['subject']),
            #'content': entry['_source']['content']
            'content': entry['_source'],   #['content']
            'doc_score': entry['_score']
            #'images' : get_images(entry['_id'])
        })
    #print(structured_results)
    return structured_results

def process_search_data_reports(results):
    """
    Process results in a general search result, running the mapping function
    for each result and preparing other general data for being shown in
    templates (such as quoting the subject and including the index).
    :param results: List of GMeta results, which would be the r.data['gmeta']
    in from a simple query to Globus Search. See here:
    https://docs.globus.org/api/search/schemas/GMetaResult/
    :return: A list of search results:


    """
    field_mod_name, field_func_name = settings.SEARCH_MAPPER
    field_mod = import_module(field_mod_name)
    field_mapper = getattr(field_mod, field_func_name, default_search_mapper)
    service_mod_name, service_func_name = t_settings.ENTRY_SERVICE_VARS_MAPPER
    service_mod = import_module(service_mod_name)
    service_mapper = getattr(service_mod, service_func_name,
                             default_service_mapper)
    structured_results = []
    for entry in results:
        #print(entry)
        structured_results.append({
            'subject': quote_plus(entry['_id']),     #['subject']),
            #'content': entry['_source']['content']
            'content': entry['_source'],   #['content']
            'doc_score': entry['_score']
        })
    #print('RESULTS RETURNED: ' + str(len(structured_results)))
    return structured_results


def get_pagination(total_results, offset,
                   per_page=settings.SEARCH_RESULTS_PER_PAGE):
    """
    Prepare pagination according to Globus Search. Since Globus Search handles
    returning paginated results, we calculate the offsets and send along which
    results and how many.

    Returns: dict containing 'current_page' and a list of pages
    Example:
        {
        'current_page': 3,
        'pages': [{'number': 1},
           {'number': 2},
           {'number': 3},
           {'number': 4},
           {'number': 5},
           {'number': 6},
           {'number': 7},
           {'number': 8},
           {'number': 9},
           {'number': 10}]}
    pages: contains info which is easy for the template engine to render.
    """

    if total_results > per_page * settings.SEARCH_MAX_PAGES:
        page_count = settings.SEARCH_MAX_PAGES
    else:
        page_count = total_results // per_page or 1
    pagination = [{'number': p + 1} for p in range(page_count)]

    return {
        'current_page': offset // per_page + 1,
        'pages': pagination
    }

def get_filters(filters):
    """
    Get Globus Search filters for each facet. Currently only supports
    "match_all".

    :param filters: A dict where the keys are filters and the values are a
    list of elements to filter on.
    :return: a list of formatted filters ready to send off to Globus Search

    Example:
        {'elements': ['O', 'H'], 'publication_year': ['2017', '2018']}
    Returns:
        List of GFilters, suitable for Globus Search:
        https://docs.globus.org/api/search/schemas/GFilter/

    """
    return [{
        'type': 'match_all',
        'field_name': name,
        'values': values
    } for name, values in filters.items()]

def get_facets(search_result, search_schema, filters):
    """Prepare facets for display. Globus Search data is removed from results
    and the results are ordered according to the facet map. Empty categories
    are removed and any filters the user checked are tracked.

    :param search_result: A raw search result from Globus Search
    :param search_schema: SEARCH_SCHEMA in settings.py
    :param filters: A dict of user-selected filters, an example like this:
        {'searchdata.contributors.value': ['Cobb, Jane', 'Reynolds, Malcolm']}

    :return: A list of facets. An example is here:
        [
            {
            'name': 'Contributor'
            'buckets': [{
                   'checked': False,
                   'count': 4,
                   'field_name': 'searchdata.contributors.contributor_name',
                   'value': 'Cobb, Jane'},
                  {'checked': True,
                   'count': 4,
                   'field_name': 'searchdata.contributors.contributor_name',
                   'value': 'Reynolds, Malcolm'}
                   # ...<More Buckets>
                   ],
            },
            # ...<More Facets>
        ]

      """
    #facets = search_result.data.get('facet_results', [])
    facets = search_result
    # Remove facets without buckets so we don't display empty fields
    #pruned_facets = {f['name']: f['buckets'] for f in facets if f['buckets']}
    cleaned_facets = []
    if facets:
        #print(facets)
        #print(len(facets))
        keys = facets.keys()
        pruned_facets = {}
        for k in keys:
            #print(k)
            #print(facets.get(k)['buckets'])
            pruned_facets[k] = facets.get(k)['buckets']
    
        #print(pruned_facets)
        for f in search_schema['facets']:   # this is using the search_fields.json loaded from SEARCH SCHEMA file
            #print(f)
            buckets = pruned_facets.get(f['field_name'])
            if buckets:
                facet = {'name': f['name'], 'field_name':f['field_name'],'buckets': []}
                #print("made it here")
                for bucket in buckets:
                    #print(bucket)
                    facet['buckets'].append({
                        #'count': bucket['count'],
                        'count': bucket['doc_count'],
                        'value': bucket['key'],
                        #'value': bucket['value'],
                        'field_name': f['field_name'],
                        'checked': bucket['key'] in 
                        filters.get(f['field_name'], [])
                    })
                #print(facet)
                cleaned_facets.append(facet)

    return cleaned_facets

def my_mapper(entry, schema):
    # Automap fields in settings.SEARCH_SCHEMA
    fields = default_search_mapper(entry, schema)
    # Dates from my search index are formatted: '2018-12-30'. Format them into
    # datetimes for Django templates. Disregard other info in ['dates']['data']
    if fields.get('dates'):
        fields['dates']['data'] = [
            {'value': datetime.strptime(d['value'], '%Y-%m-%d')}
            for d in fields['dates']['data'] if d.get('value')
        ]
    return fields

def general_mapper(entry, schema):
    fields = {k: {'field_title': schema[k].get('field_title', k),
                  'data': v
                  } for k, v in entry[0].items() if schema.get(k)
              }
    #print(fields)
    return fields


def service_var_mapper(entry, schema):
    pass

# def get_images(patient_id):

#     try:

#         context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
#         context.verify_mode = ssl.CERT_NONE   # ignore the cert req

#         conn = http.client.HTTPSConnection("openslide", port=5000, context=context)

#         headers = {
#             'cache-control': "no-cache",
#             'postman-token': "3fecc1a7-fd6f-fea8-70ff-a0b493406d03"
#             }

#         req_url = "/get_patient_images/" + patient_id

#         conn.request("GET", req_url, headers=headers)

#         res = conn.getresponse()
#         data = res.read()

#         js = data.decode("utf-8")
#         jsres = json.loads(js)

#         return jsres['images']

#     except Exception as e:
#         print(e)
#         raise e

def get_imagemap():

    try:

        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE   # ignore the cert req

        conn = http.client.HTTPSConnection(settings.OPENSLIDE_URL, port=settings.OPENSLIDE_PORT, context=context)

        headers = {
            'cache-control': "no-cache",
            'postman-token': "3fecc1a7-fd6f-fea8-70ff-a0b493406d03"
            }

        req_url = "/image_count_map"

        conn.request("GET", req_url, headers=headers)

        res = conn.getresponse()
        data = res.read()

        js = data.decode("utf-8")
        jsres = json.loads(js)
        #print('*******************************************************')
        #print(jsres)
        #print(type(jsres))
        #print('*******************************************************')
        return jsres
    except Exception as e:
        print(e)
        raise e

def fetch_thumbnail(image_name):

    try:

        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE   # ignore the cert req

        conn = http.client.HTTPSConnection(settings.OPENSLIDE_URL, port=settings.OPENSLIDE_PORT, context=context)

        headers = {
            'cache-control': "no-cache",
            'postman-token': "3fecc1a7-fd6f-fea8-70ff-a0b493406d03"
            }

        req_url = "/get_image_thumbnail/" + image_name

        conn.request("GET", req_url, headers=headers)

        res = conn.getresponse()
        data = res.read()

        js = data.decode("utf-8")
        print('****fetch_thumbnail***************************************************')
        print(js)
        #print(type(jsres))
        print('*******************************************************')
        return js
    except Exception as e:
        print(e)
        raise e  

def fetch_slides(slide_id):

    try:

        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE   # ignore the cert req

        conn = http.client.HTTPSConnection(settings.OPENSLIDE_URL, port=settings.OPENSLIDE_PORT, context=context)

        headers = {
            'cache-control': "no-cache",
            'postman-token': "3fecc1a7-fd6f-fea8-70ff-a0b493406d03"
            }

        req_url = "/get_sample_images/"+ slide_id

        conn.request("GET", req_url, headers=headers)

        res = conn.getresponse()
        data = res.read()

        js = data.decode("utf-8")
        jsres = json.loads(js)
        print('****fetch_slides***************************************************')
        print(jsres)
        print(type(jsres))
        print('*******************************************************')
        return jsres
    except Exception as e:
        print(e)
        raise e
