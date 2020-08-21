import time
import urllib.parse
from json import JSONDecodeError
from typing import Any
from typing import Dict
from typing import Optional

from locust import SequentialTaskSet  # type: ignore
from requests.cookies import RequestsCookieJar


def query_replace(
    url_struct: urllib.parse.ParseResult, replacements: Dict[str, Optional[Any]]
) -> urllib.parse.ParseResult:
    """
    Replaces query parameters in an url
    """
    query_params = dict(urllib.parse.parse_qsl(url_struct.query))
    new_query = {
        k: v if (k not in replacements) else replacements[k]
        for k, v in query_params.items()
    }
    final_struct = url_struct._replace(query=urllib.parse.urlencode(new_query))
    return final_struct


def param_replace(
    url_struct: urllib.parse.ParseResult, keyword: str, value: str
) -> urllib.parse.ParseResult:
    """
    Replace parts of an url path that are used as parameters in GET requests
    """
    if value is None:
        return url_struct

    final_struct = url_struct
    if keyword in url_struct.path:
        path = url_struct.path.split("/")
        position = path.index(keyword)
        # check if next part is actually a parameter:
        if path[position + 1] != "":
            path[position + 1] = value
            final_struct = url_struct._replace(path="/".join(path))
    return final_struct


class ClientWrapper(object):
    """
    Client created to proxy and modify the requests before they are sent via locust
    Requests will be processed to modify the params from the original har file
    and adjust them to the current session.
    The real client is the task.locust.client
    """

    csrf_cookie_name = None

    def __init__(self, task: SequentialTaskSet):
        self.task = task
        # This is the real client (usually a locust.clients.HttpSession):
        self.client = task.locust.client
        parsed_url = urllib.parse.urlparse(self.client.base_url)
        netloc = parsed_url.hostname
        if parsed_url.port:
            netloc += ":%d" % parsed_url.port
        self.server_url = netloc

    @classmethod
    def set_csrf_cookie_name(cls, cookies: RequestsCookieJar):
        """
        Cookie name used for csrf is an option that
        can change.
        Let's assume the name always contains the substring 'csrf'
        """
        if not cls.csrf_cookie_name:
            for cookie in cookies:
                if "csrf" in cookie.name:
                    cls.csrf_cookie_name = cookie.name
                    break

    def process_url(self, url: str) -> str:

        # First, let's replace the query parameters that are depending on the session: cache_key & user_id
        replacements = {
            "contentCacheKey": StudioUserBehavior.content_cache_key,
            "user_id": self.task.user_id,
        }
        url_struct = query_replace(urllib.parse.urlparse(url), replacements)

        # Then, let's replace the id parts that are inserted as part
        # of the url path, usually loggers ids
        print(url)
        # params_replacements = {k: self.task.logs[k] for k in loggers}
        # if self.task.user_id:
        #     params_replacements["userprogress"] = self.task.user_id
        #     params_replacements["facilityuser"] = self.task.user_id
        # for param_id in params_replacements:
        #     url_struct = param_replace(
        #         url_struct, param_id, params_replacements[param_id]
        #     )

        # Finally, reconstruct the new url and return it:
        url_struct = url_struct._replace(netloc=self.server_url)
        return url_struct.geturl()

    def process_headers(self, headers):
        items_to_replace = {"User-Agent": "velox", "Host": self.server_url}
        if "X-CSRFToken" in headers:
            if not ClientWrapper.csrf_cookie_name:
                ClientWrapper.set_csrf_cookie_name(self.client.cookies)
            items_to_replace["X-CSRFToken"] = self.client.cookies[
                ClientWrapper.csrf_cookie_name
            ]
        return {
            k: v if (k not in items_to_replace) else items_to_replace[k]
            for k, v in headers.items()
        }

    def process_json(self, payload):
        # use the provided credentials:
        payload_to_replace = {
            "username": StudioUserBehavior.user,
            "password": StudioUserBehavior.password,
        }
        # facility management:
        if "facility" in payload:
            if self.task.facility_id:
                payload_to_replace["facility"] = self.task.facility_id
            else:
                # remove facility, supposing there's only one facility so kolibri will find it:
                del payload["facility"]

        if "user" in payload:
            payload_to_replace["user"] = self.task.user_id
        # in case sessionlog or summarylog are in the payload:
        # for logger in loggers:
        #     logger_slim = logger.replace("content", "")
        #     if logger_slim in payload:
        #         payload_to_replace[logger_slim] = self.task.logs[logger]

        return {
            k: v if (k not in payload_to_replace) else payload_to_replace[k]
            for k, v in payload.items()
        }

    def process_request(self, **kwargs):
        kwargs["url"] = self.process_url(kwargs["url"])
        kwargs["name"] = kwargs["url"]
        kwargs["headers"] = self.process_headers(kwargs["headers"])
        if "json" in kwargs:
            kwargs["json"] = self.process_json(kwargs["json"])
        return kwargs

    def get(self, **kwargs):
        return self.client.get(**self.process_request(**kwargs))

    def post(self, **kwargs):
        return self.client.post(**self.process_request(**kwargs))

    def put(self, **kwargs):
        return self.client.put(**self.process_request(**kwargs))

    def patch(self, **kwargs):
        return self.client.patch(**self.process_request(**kwargs))

    def delete(self, **kwargs):
        return self.client.delete(**self.process_request(**kwargs))


class StudioUserBehavior(SequentialTaskSet):
    # user & password temporal, to be read from a file
    user = "admin"
    password = "pass"
    content_cache_key = None

    def __init__(self, parent):
        super(StudioUserBehavior, self).__init__(parent)
        if StudioUserBehavior.content_cache_key is None:
            StudioUserBehavior.content_cache_key = int(time.time())
        self.user_id = None
        self.facility_id = None
        # self.logs = {k: None for k in loggers}

    def parse_response(self, response):
        try:
            response_data = response.json()
            if isinstance(response_data, list) and response_data:
                response_data = response_data[0]
        except JSONDecodeError:
            response_data = None
        if (
            response.status_code == 400
            or response.status_code == 404
            or response.status_code == 403
            or response.status_code >= 500
        ):
            print(
                "&&&&&&&& {reason} ERROR: {url}".format(
                    url=response.url, reason=response.reason
                )
            )

        elif response_data:
            if "auth" in response.url:
                if self.user_id is None:
                    self.user_id = response_data.get("user_id", None)
                if self.facility_id is None:
                    self.facility_id = response_data.get("facility_id", None)
            # else:
            #     for log in loggers:
            #         if log in response.url:
            #             if log == "contentsummarylog":
            #                 if response_data.get("currentmasterylog", None):
            #                     self.logs["masterylog"] = response_data[
            #                         "currentmasterylog"
            #                     ]["id"]
            #             if response_data.get("id", None):
            #                 self.logs[log] = response_data.get("id", None)
            #             break

    @property
    def client(self):
        """
        Reference to the :py:attr:`client <locust.core.Locust.client>` attribute of the root
        Locust instance.
        """
        return ClientWrapper(self)
