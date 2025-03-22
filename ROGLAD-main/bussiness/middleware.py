
from django.db import IntegrityError
from django.utils.deprecation import MiddlewareMixin

from bussiness.models import ErrorReport


class ErrorHandlingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, Exception):            
            error_type = type(exception).__name__
            error_message = str(exception)
            ErrorReport.objects.create(code=error_type,error=error_message)
  
