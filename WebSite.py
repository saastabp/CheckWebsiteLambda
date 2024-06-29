import urllib.request
import logging
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class WebSite:

    def __init__(self, site_obj: dict):
        self.url = site_obj.get('url', None)
        self.http_status = site_obj.get('http_status', None)
        self.http_reason = site_obj.get('http_reason', None)
        self.last_checked = site_obj.get('last_checked', None)
        self.last_changed = site_obj.get('last_changed', None)
        self.is_changed = False
        self.is_up = site_obj.get('is_up', False)
        self.is_slow = site_obj.get('is_slow', False)

    def get_url(self):
        """
        Get the URL of the website
        Returns
        -------
        String: the URL of the website
        """
        return self.url

    def get_http_status(self):
        return self.http_status

    def get_http_reason(self):
        return self.http_reason

    def get_last_changed(self):
        return self.last_changed

    def set_last_changed(self, last_changed: datetime):
        if last_changed is not None:
            self.last_changed = last_changed.isoformat()
        else:
            self.last_changed = None

    def get_last_checked(self):
        return self.last_checked

    def set_last_checked(self, last_checked: datetime):
        if last_checked is not None:
            self.last_checked = last_checked.isoformat()
        else:
            self.last_checked = None

    def get_is_changed(self):
        return self.is_changed

    def check_website(self, **kwargs):
        slow_response_threshold = kwargs.get('SlowResponseSeconds', 5)
        current = WebSite(self.__dict__)
        try:
            start_time = datetime.now()
            u = urllib.request.urlopen(self.url)
            response_time = datetime.now() - start_time
            current.http_status = u.status
            current.http_reason = u.reason if u.reason else "OK"
            current.elapsed_time = round(response_time.total_seconds())
            current.is_up = True

            if current.elapsed_time > slow_response_threshold:
                current.is_slow = True
            else:
                current.is_slow = False

        except HTTPError as he:
            current.http_status = he.code
            current.http_reason = he.reason
        except URLError as ue:
            current.http_status = "N/A"
            current.http_reason = f"{str(ue)}"

        if current.http_status != self.http_status:
            current.set_last_changed(datetime.now(timezone.utc))
            current.is_changed = True

        current.set_last_checked(datetime.now(timezone.utc))

        return current
