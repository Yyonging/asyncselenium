import aiohttp
import logging

try:
    from urllib import parse
except ImportError:  # above is available in py3+, below is py2.7
    import urlparse as parse

from selenium.webdriver.remote import utils
from selenium.webdriver.remote.errorhandler import ErrorCode
from selenium.webdriver.remote.remote_connection import RemoteConnection

LOGGER = logging.getLogger(__name__)

class AsyncRemoteConnection(RemoteConnection):
    '''Async connection with the async remote webdriver server
    '''

    def _request(self, method, url, body=None):

        async def __async_request():
            nonlocal body
            LOGGER.debug('%s %s %s' % (method, url, body))

            parsed_url = parse.urlparse(url)
            headers = self.get_remote_connection_headers(parsed_url, self.keep_alive)
            resp = None
            if body and method != 'POST' and method != 'PUT':
                body = None

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.request(method, url, data=body) as resp:
                    statuscode = resp.status
                    data = await resp.text()
                    try:
                        if 300 <= statuscode < 304:
                            return self._request('GET', resp.headers.get('location'))
                        if 399 < statuscode <= 500:
                            return {'status': statuscode, 'value': data}
                        content_type = []
                        if resp.headers.get('Content-Type') is not None:
                            content_type = resp.headers.get('Content-Type').split(';')
                        if not any([x.startswith('image/png') for x in content_type]):

                            try:
                                data = utils.load_json(data.strip())
                            except ValueError:
                                if 199 < statuscode < 300:
                                    status = ErrorCode.SUCCESS
                                else:
                                    status = ErrorCode.UNKNOWN_ERROR
                                return {'status': status, 'value': data.strip()}

                            # Some of the drivers incorrectly return a response
                            # with no 'value' field when they should return null.
                            if 'value' not in data:
                                data['value'] = None
                            return data
                        else:
                            data = {'status': 0, 'value': data}
                            return data
                    finally:
                        LOGGER.debug("Finished Request")
        return __async_request


