import logging

logger = logging.getLogger(__name__)


class StoreLastURLMiddleware:
    """
    保存用户访问页面的 URL
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        只保存非搜索页面的 URL
        """
        if 'search' not in request.path:
            logger.debug(f"Saving URL: {request.build_absolute_uri()} for {request.path}")
            request.session['last_url'] = request.build_absolute_uri()
        else:
            logger.debug(f"Search page accessed: {request.path}, no URL saved.")

        response = self.get_response(request)
        return response
