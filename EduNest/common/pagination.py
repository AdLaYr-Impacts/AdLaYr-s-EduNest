import math
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.response import Response


class StandardPagination(LimitOffsetPagination):
    """
    StandardLimitOffsetPagination
    """

    default_limit = 10     
    limit_query_param = 'limit'     
    offset_query_param = 'offset'     
    max_limit = 100

    def get_paginated_response(self, data):
         limit = self.get_limit(self.request)
         offset = self.offset
         total_records = self.count

         current_page = (offset // limit) + 1
         total_pages = math.ceil(total_records / limit) if limit else 1

         return Response({
             'success': True,
             'message': 'Data fetched successfully',
             'data': data,
             'pagination': {
                 'current_page': current_page,
                 'total_pages': total_pages,
                 'total_records': total_records,
                 'next': self.get_next_link(),
                 'previous': self.get_previous_link()
             }
         })


class StandardPageNumberPagination(PageNumberPagination):
    """
    PageNumberPagination
    """

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'message': 'Data fetched successfully',
            'data': data,
            'pagination': {
                'current_page': self.page.number,
                'total_pages': self.page.paginator.num_pages,
                'total_records': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            }
        })
