# Copyright (c) 2013 Martin Abente Lahaye. - tch@sugarlabs.org
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import os
import json

from harvest_dextrose import is_dextrose, dextrose_version
from harvest_dextrose import get_gconf_default_client
from harvest_dextrose import get_serial_number
from harvest_dextrose import get_uuid, get_build

if is_dextrose:
    import ceibal.laptops

if dextrose_version == "dextrose3":
    from sugar.datastore import datastore
else:
    from sugar3.datastore import datastore

from croplog import CropLog
from croplog import session_crop, activities_crop, gnome_crop

GNOME_APPS_LOG = '/home/olpc/.olpc-gnome-stats'
SUGAR_ACTS_LOG = '/home/olpc/.olpc-sugar-stats'
SESSIONS_LOG = '/home/olpc/.olpc-launch-stats'

class CropErrorNotReady:
    pass


class Crop(object):

    VERSION = '000312'

    ARM_SN_PATH = '/ofw/serial-number/serial-number'
    X86_SN_PATH = '/proc/device-tree/serial-number'
    AGE_PATH = '/desktop/sugar/user/birth_timestamp'
    GENDER_PATH = '/desktop/sugar/user/gender'
    BUILD_PATH = '/boot/olpc_build'
    UPDATED_PATH = '/var/lib/misc/last_os_update.stamp'

    def __init__(self, start=None, end=None):
        self._start = start
        self._end = end
        self._data = None

    def serialize(self):
        if not self._data:
            raise CropErrorNotReady()
        return json.dumps(self._data)

    def grown(self):
        if not self._data:
            raise CropErrorNotReady()
        if not self._data[2].keys() and not self._data[3] and not self._data[4]:
            return False
        return True

    def characterizable(self):
        """ check if all learner characteristics are available """
        if self._serial_number() is None or \
           self._age() is None or \
           self._gender() is None:
            return False
        return True

    def collect(self):
        self._data = []
        self._data.append(self._laptop())
        self._data.append(self._learner())
        self._data.append(self._activities())
        self._data.append(self._gnome_apps())
        self._data.append(self._sessions())
        #self._data.append(self._connectivity())

    def _laptop(self):
        laptop = []
        laptop.append(self._serial_number())
        laptop.append(self._uuid())
        laptop.append(self._model())
        laptop.append(self._update_version())
        laptop.append(self._build())
        laptop.append(self._updated())
        laptop.append(self._collected())
        return laptop

    def _serial_number(self):
        if is_dextrose:
            return get_serial_number()

        path = None
        if os.path.exists(self.ARM_SN_PATH):
            path = self.ARM_SN_PATH
        elif os.path.exists(self.X86_SN_PATH):
            path = self.X86_SN_PATH
        if path is not None:
            with open(path, 'r') as file:
                return file.read().rstrip('\0\n')
        return None

    def _uuid(self):
        if not is_dextrose:
            return None

        return get_uuid()

    def _model(self):
        if not is_dextrose:
            return None
        xo = ceibal.laptops.XO()
        model = None
        if hasattr(xo, '_model'):
            model = xo._model.replace('\x00', '')
        else:
            model = ceibal.laptops.get_model_laptop().replace('\x00', '')
        return model

    def _update_version(self):
        if not is_dextrose:
            return None
        xo = ceibal.laptops.XO()
        return xo.get_update_version(xo._update_type)

    def _build(self):
        if not is_dextrose:
            if os.path.exists(self.BUILD_PATH):
                with open(self.BUILD_PATH, 'r') as file:
                    return file.read().rstrip('\0\n')
        else:
            return get_build()

    def _updated(self):
        if os.path.exists(self.UPDATED_PATH):
            return int(os.stat(self.UPDATED_PATH).st_mtime)
        return None

    def _collected(self):
        return self._end

    def _learner(self):
        learner = []
        learner.append(self._age())
        learner.append(self._gender())
        return learner

    def _age(self):
        client = get_gconf_default_client()
        age = client.get_int(self.AGE_PATH)
        if not age:
            return 0
        return age

    def _gender(self):
        client = get_gconf_default_client()
        gender = client.get_string(self.GENDER_PATH)
        if not gender:
            return ''
        return gender

    def _activities(self):
        croplog = CropLog(SUGAR_ACTS_LOG, activities_crop,
                          self._start, self._end)
        return croplog.collect()

    def _gnome_apps(self):
        croplog = CropLog(GNOME_APPS_LOG, gnome_crop,
                          self._start, self._end)
        return croplog.collect()

    def _sessions(self):
        croplog = CropLog(SESSIONS_LOG, session_crop,
                          self._start, self._end)
        return croplog.collect()

    def _connectivity(self):
        croplog = CropLog('/home/olpc/.olpc-connectivity', connectivity_crop,
                          self._start, self._end)
        return croplog.collect()


def logs_are_clean():
    for log_path in (GNOME_APPS_LOG, SUGAR_ACTS_LOG, SESSIONS_LOG):
        if os.path.exists(log_path) and os.stat(log_path).st_size > 0:
            return False
    return True

def clean_logs():
    for log_path in (GNOME_APPS_LOG, SUGAR_ACTS_LOG, SESSIONS_LOG):
        open(log_path, 'w').close()


def _bool(value):
    if not value:
        return None
    if value == '1':
        return True
    return False


def _int(value):
    if not value:
        return None
    return int(value)

def _str(value):
    if not value:
        return None
    return str(value)
