import logging
import json
from os.path import basename
from urllib.parse import unquote
import globus_sdk
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from globus_portal_framework.search import (settings, utils)
from globus_portal_framework.transfer import settings as t_settings
from globus_portal_framework import (preview, helper_page_transfer,
                                     get_helper_page_url, parse_globus_url,
                                     get_subject, post_search,
                                     PreviewException, PreviewURLNotFound,
                                     ExpiredGlobusToken,
                                     check_exists)

log = logging.getLogger(__name__)

def index(request):    
    context = {}

    context['es_is_active'] = utils.checkES_connection()

    if not request.user.is_authenticated:
        return redirect('%s/globus?next=%s' % (settings.LOGIN_URL, request.path))

    return render(request, 'index.html', context)

def searchBAK(request):

    context = {}
    filters = {}
    query = request.GET.get('q') or request.session.get('query') or \
        settings.DEFAULT_QUERY
    print("search..."+str(query))    
    context['search'] = post_search(settings.SEARCH_INDEX, query, filters, request.user, request.GET.get('page', 1))
    request.session['search'] = {
            'full_query': request.get_full_path(),
            'query': query,
            'filters': filters,
            #'samples': aggregate(context['search']['facets'], 'Sample Types'),
            #'histology': aggregate(context['search']['facets'], 'Histology'),
            #'gender': aggregate(context['search']['facets'], 'Gender'),
            #'vitals': aggregate(context['search']['facets'], 'Vitals')
        }
    #print(context)
    return render(request, 'search.html', context)

def search(request):
    """
    Search the index configured in settings.SEARCH_INDEX with the queryparams
    'q' for query, 'filter.<filter>' for facet-filtering, 'page' for pagination
    If the user visits this page again without a search query, we auto search
    for them again using their last query. If the user is logged in, they will
    automatically do a credentialed search for Globus Search to return
    confidential results. If more results than settings.SEARCH_RESULTS_PER_PAGE
    are returned, they are paginated (Globus Search does the pagination, we
    only do the math to calculate the offset).

    Query Params
    q: key words for the users search. Ex: 'q=foo*' will search for 'foo*'

    filter.: Filter results on facets defined in settings.SEARCH_SCHEMA. The
    syntax for filters using query params is:
    '?filter.<filter_type>=<filter_value>, where 'filter.<filter_type>' is
    defined in settings.SEARCH_SCHEMA and <filter_value> is any value returned
    by Globus Search contained within search results. For example, we can
    define a filter 'mdf.elements' in our schema, and use it to filter all
    results containing H (Hydrogen).

    page: Page of the search results. Number of results displayed per page is
    configured in settings.SEARCH_RESULTS_PER_PAGE, and number of pages can be
    controlled with settings.SEARCH_MAX_PAGES.

    Templates:
    The resulting page is templated using the 'search.html' template, and
    'search-results.html' and 'search-facets.html' template components. The
    context required for searches is shown here:

    {
        'search': {
            'facets': [
                {'buckets': [{'field_name': 'mdf.resource_type',
                            'value': 'record'}],
                'name': 'Resource Type'},
                <More Facets>...
            ],
            'pagination': {'current_page': 1, 'pages': [{'number': 1}]},
            'search_results': [
            {
                'subject': '<Globus Search Subject>',
                'fields': {
                    'titles': {'field_name': 'titles',
                                                    'value': '<Result Title>'},
                    'version': {'field_name': 'version', 'value': '0.3.2'},
                    '<field_name>': {'field_name': '<display_name>',
                                     'value': '<field_value>'},
                    'foo_field': {'field_name': 'foo', 'value': 'bar'}
                }
            }, <More Search Results>...]
        }
    }

    Example request:
    http://myhost/?q=foo*&page=2&filter.my.special.filter=goodresults
    """
    context = {}
    query = request.GET.get('q') or request.session.get('query') or \
        settings.DEFAULT_QUERY
    #print(query)
    print('openslide url: {}'.format(settings.OPENSLIDE_URL))
    openslide = '{}:{}'.format(settings.OPENSLIDE_URL, settings.OPENSLIDE_PORT)
    if query:
        filters = {k.replace('filter.', ''): request.GET.getlist(k)
                   for k in request.GET.keys() if k.startswith('filter.')}
        context['search'] = post_search(settings.SEARCH_INDEX, query, filters,
                                        request.user,
                                        request.GET.get('page', 1))
        print(filters)
        request.session['search'] = {
            'full_query': request.get_full_path(),
            'query': query,
            'openslide': openslide,
            'samples_agg': aggregate(context['search']['facets'], 'Sample Types'),
            'samples_pres_agg': aggregate(context['search']['facets'], 'Sample Preservation Method'),
            'samples_site_agg': aggregate(context['search']['facets'], 'Sample Tissue Type'),
            'show_results': 'True',
            'HELLO': 'hi',
            'display_fields': utils.get_display_fields()
#            'aggregate': aggregate(context['search']['facets'], 'Age at Dx'),
#            'histology': aggregate(context['search']['facets'], 'Histology'),
#            'gender': aggregate(context['search']['facets'], 'Gender'),
#            'vitals': aggregate(context['search']['facets'], 'Vitals')
        }
        #get_multi_dimension_data(context['search']['search_results'])
        #print(context['search'])
        #print("Filters......")
        #print(context['search']['pagination'])
        #print(request.session['aggregate'])
        # get some simple aggregates
        #print("Doing a query")
        #print(request.get_full_path())
        #print(query)
        #context['aggregate'] = get_aggregates(context['search']['facets'])
    else:  # this is executed when no query is performed
        print("No query was entered")
        try:
            query = "*"
            filters = {}
            results = {}
            request.session['search'] = {}
            context['search'] = post_search(settings.SEARCH_INDEX, query, filters,
                                        request.user,
                                        request.GET.get('page', 1))            

            request.session['search'] = {
                'full_query': request.get_full_path(),
                'query': query,
                'openslide': openslide,                
                'samples_agg': aggregate(context['search']['facets'], 'Sample Types'),
                'samples_pres_agg': aggregate(context['search']['facets'], 'Sample Preservation Method'),
                'samples_site_agg': aggregate(context['search']['facets'], 'Sample Tissue Type'),                
                'show_results': 'False',
                'display_fields': utils.get_display_fields()
            }

        except ExpiredGlobusToken as ex:
            log.debug(ex)
            return render(request, 'login-error.html')
        except Exception as e:
            print("in exception....")
            print(e)
            log.debug(e)
            pass        
    return render(request, 'search.html', context)

def get_multi_dimension_data(data):
    # structure of the data {'subject': 'https%3A%2F%2Fcr3.pitt.edu%2Fsubject%2F112389', 
    #                           'fields': {'age': {'field_title': 'Age', 'data': '89'},...
    try:
        for x in data:
            print(x['fields']['age']['data'])
    except Exception as e:
        print(e)
        log.error(e)
        pass

# creates an array of summary data using the filter data
def get_summary_data(data, which_bucket):
    sum_data = []
    sdata = ""
    idx = -1
    i = 0
    try:
        for x in data:
            if x['name'] == which_bucket:
                idx = i
            i = i + 1
        if idx > -1:
            #print(data[idx]['buckets'])
            try:
                if which_bucket == 'Age at Dx':  # this is a special case, to get ages order a specific way
                    sum_data = get_age_dx_list(data[idx]['buckets'])
                else:
                    for rec in data[idx]['buckets']:
                        s = '{"label":"' + str(rec["value"]) + '","value":' + str(rec["count"]) + "}"
                        sum_data.append(json.loads(s))

                #sdata = '|'.join(sum_data)
                #print(sum_data)
            except Exception as ex:
                #print("in get sum")
                print(ex)
                log.error(ex)
                pass
    except Exception as e:
        pass

    return sum_data  #sdata

# special function to order the age at dx by label, otherwise its sorted by values not label
def get_age_dx_list(buckets):
    age_order = ["<21", "21-34", "35-44", "45-54", "55-64", "65-74", "75-84","85+"]
    age_range = []

    for l in age_order:
        for rec in buckets:
            if l == rec["value"]:
                #print(l + " == " + str(rec["value"]))
                s = '{"label":"' + str(rec["value"]) + '","value":' + str(rec["count"]) + "}"
                age_range.append(json.loads(s))
    return age_range

# generalized function to format aggregate data. the bucket corresponds to the facet name
def aggregate(data, which_bucket):
    #print("aggregate2")
    summerized = get_summary_data(data, which_bucket)
    #print(summerized)
    total = 0
    for x in summerized:
        total += x['value']

    final = [ {"key":which_bucket,
            "values": summerized,
            "total" : total}]
    #print("----------------------")
    #print(final)
    return final

def cohort_request(request):    
    return render(request, 'cohort-request.html')    

# facet-search, allow user to select multiple values
# def advanced_filters(request):
#     context = {}
#     query = request.GET.get('q') or request.session.get('query') or \
#         settings.DEFAULT_QUERY
#     if query:
#         if query == "*":
#             query = ""

#         filters = {k.replace('filter.', ''): request.GET.getlist(k)
#                    for k in request.GET.keys() if k.startswith('filter.')}
#         #context['search'] = post_search(settings.SEARCH_INDEX, query, filters,
#         #                                request.user,
#         #                                request.GET.get('page', 1))
#         request.session['search'] = {
#             'full_query': request.get_full_path(),
#             'query': query,
#             'filters': filters}
#         #    'aggregate': aggregate(context['search']['facets'])
#         #}
#     print("advanced_filters......" + str(query))
        
#     return HttpResponse(request, status=204)  # just return the updated requests

#def submit_advanced(request):
#     return HttpResponse(request, status=204) 

def submit_advanced(request):
    context = {}
    #filters = request.GET.get('filters') or request.session.get('filters') 
    #print(request)
    filters = request.GET.get('filters') or request.session.get('filters') 
    filters = {k.replace('filter.', ''): request.GET.getlist(k)
                for k in request.GET.keys() if k.startswith('filter.')}

    #filters = request.session['search']['filters']
    query = request.session['search']['query']
    full_query = request.get_full_path()
    print("submit_advanced...")
    print(query)
    #print(full_query)

    #if query:
    #    filters = {k.replace('filter.', ''): request.GET.getlist(k)
    #               for k in request.GET.keys() if k.startswith('filter.')}
    context['search'] = post_search(settings.SEARCH_INDEX, query, filters,
                                    request.user,
                                    request.GET.get('page', 1), True)  # search with advanced flag to reformat query

    rtn_query = context['search']['query']

    if (rtn_query and rtn_query != query):
        query = rtn_query
        full_query = "search/?q=" + str(query)
        #print('QUERY STUFF')
        #print('full query: ' + str(full_query))

    request.session['search'] = {
        'full_query': full_query,
        'query': query,
        'filters': filters,
        'samples_agg': aggregate(context['search']['facets'], 'Sample Types'),
        'samples_pres_agg': aggregate(context['search']['facets'], 'Sample Preservation Method'),
        'samples_site_agg': aggregate(context['search']['facets'], 'Sample Tissue Type'),        
        'show_results': 'True',
        'display_fields': utils.get_display_fields()
#        'aggregate': aggregate(context['search']['facets'], 'Age at Dx'),
#        'histology': aggregate(context['search']['facets'], 'Histology'),
#        'gender': aggregate(context['search']['facets'], 'Gender'),
#        'vitals': aggregate(context['search']['facets'], 'Vitals')        
    }    #context['aggregate'] = get_aggregates(context['search']['facets'])
    
    #print(context['search'])
    #print(filters)
    return  render(request, 'search.html', context)

#def detail(request, subject):
def detail(request):
    """
    Load a page for showing details for a single search result. The data is
    exactly the same as the entries loaded by the index page in the
    'search_results'. The template is ultimately responsible for which fields
    are displayed. The only real functional difference between the index page
    and the detail page is that it displays only a single result. The
    detail-overview.html template is used to render the page.

    Example request:
    http://myhost/detail/<subject>

    Example context:
    {'subject': '<Globus Search Subject>',
     'fields': {
                'titles': {'field_name': 'titles', 'value': '<Result Title>'},
                'version': {'field_name': 'version', 'value': '0.3.2'},
                '<field_name>': {'field_name': '<display_name>', 'value':
                                                            '<field_value>'}
                }
    }
    """
    return render(request, 'detail-overview.html',
                  get_subject(subject, request.user))


def detail_metadata(request, subject):
    """
    Render a metadata page for a result. This is functionally the same as the
    'detail' page except it renders a detail-metadata.html instead for
    displaying tabular data about an object.
    """
    return render(request, 'detail-metadata.html',
                  get_subject(subject, request.user))


@csrf_exempt
def detail_transfer(request, subject):
    context = get_subject(subject, request.user)
    task_url = 'https://www.globus.org/app/activity/{}/overview'
    if request.user.is_authenticated:
        try:
            ep, path = parse_globus_url(unquote(subject))
            check_exists(request.user, ep, path)
            if request.method == 'POST':
                task = helper_page_transfer(request, ep, path,
                                            helper_page_is_dest=True)
                context['transfer_link'] = task_url.format(task['task_id'])
            this_url = reverse('detail-transfer', args=[subject])
            full_url = request.build_absolute_uri(this_url)
            # This url will serve as both the POST destination and Cancel URL
            context['helper_page_link'] = get_helper_page_url(
                full_url, full_url, folder_limit=1, file_limit=0)
        except globus_sdk.TransferAPIError as tapie:
            if tapie.code == 'EndpointPermissionDenied':
                messages.error(request, 'You do not have permission to '
                                        'transfer files from this endpoint.')
            elif tapie.code == 'ClientError.NotFound':
                messages.error(request, tapie.message.replace('Directory',
                                                              'File'))
            elif tapie.code == 'AuthenticationFailed' \
                    and tapie.message == 'Token is not active':
                raise ExpiredGlobusToken()
            else:
                log.error('Unexpected Error found during transfer request',
                          tapie)
                messages.error(request, tapie.message)
    return render(request, 'detail-transfer.html', context)


def detail_preview(request, subject):
    context = get_subject(subject, request.user)
    try:
        url, scope = context['service'].get('globus_http_link'), \
                     context['service'].get('globus_http_scope')
        # TODO: DEPRECATED -- Remove this "elif" block at version 0.3.0
        if (not url or not scope) and (t_settings.GLOBUS_HTTP_ENDPOINT and
                                       t_settings.PREVIEW_TOKEN_NAME):
            _, path = parse_globus_url(unquote(subject))
            context['subject_title'] = basename(path)
            url = '{}{}'.format(t_settings.GLOBUS_HTTP_ENDPOINT, path)
            scope = t_settings.PREVIEW_TOKEN_NAME
            log.warning(
                'settings.GLOBUS_HTTP_ENDPOINT and settings.PREVIEW_TOKEN_NAME'
                ' are deprecated and will be removed in a future version. '
                'Please instead retrieve the URL from the search result under '
                'the key defined by "globus_http_link" and "globus_http_scope"'
                ' in settings.ENTRY_SERVICE_VARS')
        if not url or not scope:
            log.debug('Preview URL or Scope not found. Searched '
                      'entry {} using settings.ENTRY_SERVICE_VARS, result: {}'
                      ''.format(url, scope, subject, context['service']))
            raise PreviewURLNotFound(subject)
        context['preview_data'] = \
            preview(request.user, url, scope, t_settings.PREVIEW_DATA_SIZE)
    except PreviewException as pe:
        if pe.code in ['UnexpectedError', 'ServerError']:
            log.error(pe)
        log.debug('User error: {}'.format(pe))
        messages.error(request, pe.message)
    return render(request, 'detail-preview.html', context)

def get_thumbnail(image_name):
    return fetch_thumbnail(image_name)

def get_slide_images(slide_name):
    return fetch_slides(slide_name)
