from django.urls import path
from globus_portal_framework.search.views import (index, detail, search,
                                                  detail_metadata,
                                                  detail_transfer,                                                 
                                                  detail_preview,
                                                  cohort_request,
                                                  submit_advanced,
                                                  advanced_filters)

urlpatterns = [
    # We will likely use this at some point
    # path('admin/', admin.site.urls),
    path('detail-metadata/<path:subject>', detail_metadata,
         name='detail-metadata'),
    path('detail-preview/<path:subject>', detail_preview,
         name='detail-preview'),
    path('detail-transfer/<path:subject>', detail_transfer,
         name='detail-transfer'),
    #path('detail/<path:subject>/', detail, name='detail'),
    path('cohortreq/', cohort_request, name='cohort_request'),    
    path('', index, name='index'),
    path('search/', search, name='search'),
    path('submit-advanced/', submit_advanced, name='submit_advanced'),
    path('advanced-filters/', advanced_filters, name='advanced-filters')
    
]
