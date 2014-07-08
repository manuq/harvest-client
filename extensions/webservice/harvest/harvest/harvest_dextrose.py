import os

is_dextrose = None
dextrose_version = None
try:
    import ceibal.laptops
except ImportError:
    is_dextrose = False
else:
    is_dextrose = True

def _read_file(path):
    if os.access(path, os.R_OK) == 0:
        return None

    fd = open(path, 'r')
    value = fd.read()
    fd.close()
    if value:
        value = value.strip('\n')
        return value
    else:
        return None

def get_build():
    xo = ceibal.laptops.XO()
    build_no = xo._build
    if build_no is not None:
            return build_no

    if os.path.isfile('/boot/olpc_build'):
        build_no = _read_file('/boot/olpc_build')
    elif os.path.isfile('/bootpart/olpc_build'):
        build_no = _read_file('/bootpart/olpc_build')

    if build_no is None:
        build_no = _read_file('/etc/redhat-release')

    return build_no

def get_dextrose_version(build):
    if "Version-b" in build or "Dextrose 4" in build:
        return "dextrose4"
    elif "Version-a" in build or "Dextrose 3" in build:
        return "dextrose3"
    else:
        return None

if is_dextrose:
    # please make this always match harvest-ceibal script
    # in instalador-harvest-ceibal
    build = get_build()
    dextrose_version = get_dextrose_version(build)

if is_dextrose and dextrose_version == "dextrose3":
    import gconf
    import urllib2
    import socket
    socket.setdefaulttimeout(60)
else:
    from gi.repository import GConf
    from gi.repository import Soup


def get_gconf_default_client():
    if is_dextrose and dextrose_version == "dextrose3":
        return gconf.client_get_default()
    else:
        return GConf.Client.get_default()

def get_serial_number():
    xo = ceibal.laptops.XO()
    return xo._sn


class SenderDx3(object):
    def __init__(self, url, data, api_key):
        # content_length = len(data)
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json',
            # 'Content-Length': content_length,
        }
        self._request = urllib2.Request(url, data, headers)

    def send(self):
        try:
            response = urllib2.urlopen(self._request)
        except urllib2.HTTPError, e:
            return e.getcode(), e.message
        except urllib2.URLError, e:
            return -1, e.message
        return response.getcode(), None


class SenderOriginal(object):
    def __init__(self, url, data, api_key):
        uri = Soup.URI.new(url)
        message = Soup.Message(method='POST', uri=uri)
        message.request_headers.append('x-api-key', api_key)
        message.set_request('application/json',
                            Soup.MemoryUse.COPY,
                            data, len(data))
        self._message = message

        session = Soup.SessionSync()
        session.add_feature_by_type(Soup.ProxyResolverDefault)
        self._session = session

    def send(self):
        self._session.send_message(self._message)
        status_description = Soup.status_get_phrase(self._message.status_code)
        return self._message.status_code, status_description


if is_dextrose and dextrose_version == "dextrose3":
    Sender = SenderDx3
else:
    Sender = SenderOriginal
