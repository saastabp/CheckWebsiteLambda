import urllib.request
import logging
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class WebSite:
    """
    This class represents the state of a website given by its URL.

    Represents the state of a website given by its URL.  The last known state may
    be compared to the current state to detect changes in its availability.

    All attributes except the URL are optional.  They are set by the checkWebsite method.

    Parameters
    ----------
    site_obj: dict
        A dictionary representing the current site.  This must contain at a minimum
        a 'url' entry providing the URL of the site.  All other values are optional

    Raises
    ------
    ValueError
        If the URL is invalid.
    """

    def __init__(self, site_obj: dict):
        self._url = site_obj.get('url', site_obj.get('_url', None))
        result = urlparse(self._url)
        if result.scheme and result.netloc:
            self._http_status = site_obj.get('http_status', site_obj.get('_http_status', None))
            self._http_reason = site_obj.get('http_reason', site_obj.get('_http_reason', None))
            self._last_checked = site_obj.get('last_checked', site_obj.get('_last_checked', None))
            self._last_changed = site_obj.get('last_changed', site_obj.get('_last_changed', None))
            self._elapsed_time = site_obj.get('elapsed_time', site_obj.get('_elapsed_time', None))
            self._is_changed = False
            self._is_up = site_obj.get('is_up', site_obj.get('_is_up', False))
            self._is_slow = site_obj.get('is_slow', site_obj.get('_is_slow', False))
        else:
            raise ValueError(f'Invalid URL provided: {self._url}')

    @property
    def url(self):
        return self._url

    @property
    def http_status(self):
        return self._http_status

    @http_status.setter
    def http_status(self, http_status):
        self._http_status = http_status

    @property
    def http_reason(self):
        return self._http_reason

    @http_reason.setter
    def http_reason(self, http_reason):
        self._http_reason = http_reason

    @property
    def last_checked(self):
        return self._last_checked

    @last_checked.setter
    def last_checked(self, last_checked: datetime):
        if last_checked is not None:
            self._last_checked = last_checked.isoformat()
        else:
            self._last_checked = None

    @property
    def last_changed(self):
        return self._last_changed

    @last_changed.setter
    def last_changed(self, last_changed: datetime):
        if last_changed is not None:
            self._last_changed = last_changed.isoformat()
        else:
            self._last_changed = None

    @property
    def elapsed_time(self):
        return self._elapsed_time

    @elapsed_time.setter
    def elapsed_time(self, elapsed_time):
        self._elapsed_time = elapsed_time

    @property
    def is_changed(self):
        return self._is_changed

    @is_changed.setter
    def is_changed(self, is_changed):
        self._is_changed = is_changed

    @property
    def is_up(self):
        return self._is_up

    @is_up.setter
    def is_up(self, is_up):
        self._is_up = is_up

    @property
    def is_slow(self):
        return self._is_slow

    @is_slow.setter
    def is_slow(self, is_slow):
        self._is_slow = is_slow

    def check_website(self, **kwargs):
        """
        Verify that the website is reachable and performant.  The method tries
        to open the url.  Anything other than a http status of 200 is considered
        down.  Additionally, if the website does not respond in a prescribed amount
        of time, it is marked as 'slow'.

        Parameters
        ----------
        **kwargs: dict, optional
            The optional 'SlowResponseSeconds' may be provided to specify the maximum
            number of seconds it takes for the site to be considered performant.  The
            site is considered slow if the response time exceeds this value.
            The default value is '5' seconds if this keyword is not provided.

        Returns
        -------

        """
        slow_response_threshold = kwargs.get('SlowResponseSeconds', 5)
        current = WebSite(self.__dict__)
        try:
            start_time = datetime.now()
            u = urllib.request.urlopen(self._url)
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

        if current.http_status != self._http_status or current.is_slow != self._is_slow:
            current.last_changed = datetime.now(timezone.utc)
            current.is_changed = True

        current.last_checked = datetime.now(timezone.utc)

        return current.to_dict()

    def to_dict(self):
        """
        Converts the object to a dictionary with normalized keys.  The internal keys are
        prepended with an '_' char.  This simplifies the process of reading/writing to a
        database by providing a dict whose keys do not have the '_' char.

        Returns
        -------
        dict
            A dictionary with normalized keys.
        """
        new_dict = dict()

        new_dict['url'] = self._url
        new_dict['http_status'] = self._http_status
        new_dict['http_reason'] = self._http_reason
        new_dict['is_changed'] = self._is_changed
        new_dict['last_checked'] = self._last_checked
        new_dict['last_changed'] = self._last_changed
        new_dict['elapsed_time'] = self._elapsed_time
        new_dict['is_up'] = self._is_up
        new_dict['is_slow'] = self._is_slow

        return new_dict
