from rest_framework.pagination import LimitOffsetPagination


class CustomPagination(LimitOffsetPagination):
    page_size = 6
