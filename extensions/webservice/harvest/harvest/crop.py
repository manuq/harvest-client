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
import hashlib

from gi.repository import GConf

from sugar3.datastore import datastore

from croplog import CropLog, session_crop, gnome_crop, connectivity_crop

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
        if not self._data[2].keys():
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
        laptop.append(self._build())
        laptop.append(self._updated())
        laptop.append(self._collected())
        return laptop

    def _serial_number(self):
        path = None
        if os.path.exists(self.ARM_SN_PATH):
            path = self.ARM_SN_PATH
        elif os.path.exists(self.X86_SN_PATH):
            path = self.X86_SN_PATH
        if path is not None:
            with open(path, 'r') as file:
                return hashlib.sha1(file.read().rstrip('\0\n')).hexdigest()
        return None

    def _build(self):
        if os.path.exists(self.BUILD_PATH):
            with open(self.BUILD_PATH, 'r') as file:
                return file.read().rstrip('\0\n')
        return None

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
        client = GConf.Client.get_default()
        age = client.get_int(self.AGE_PATH)
        if not age:
            return 0
        return age

    def _gender(self):
        client = GConf.Client.get_default()
        gender = client.get_string(self.GENDER_PATH)
        if not gender:
            return ''
        return gender

    def _activities(self):
        activities = {}
        entries, count = datastore.find(self._query())
        for entry in entries:
            activity_id = entry.metadata.get('activity', '')
            if activity_id not in activities:
                activities[activity_id] = []
            activities[activity_id].append(self._instance(entry))
        return activities

    def _query(self):
        query = {}
        query['timestamp'] = {}
        if self._start:
            query['timestamp']['start'] = self._start
        if self._end:
            query['timestamp']['end'] = self._end
        return query

    def _instance(self, entry):
        instance = []
        instance.append(entry.get_object_id())
        instance.append(_int(entry.metadata.get('filesize', None)))
        instance.append(_int(entry.metadata.get('creation_time', None)))
        instance.append(_int(entry.metadata.get('timestamp', None)))
        instance.append(self._buddies(entry))
        instance.append(_bool(entry.metadata.get('share-scope', None)))
        instance.append(_bool(entry.metadata.get('title_set_by_user', None)))
        instance.append(_bool(entry.metadata.get('keep', None)))
        instance.append(_str(entry.metadata.get('mime_type', None)))
        instance.append(self._launches(entry))
        return instance

    def _buddies(self, entry):
        buddies = entry.metadata.get('buddies', None)
        if not buddies:
            return None
        return len(json.loads(buddies).values())

    def _launches(self, entry):
        metadata_list = entry.metadata.get('launch-times', None)
        if metadata_list is None:
            return []

        metadata_list = map(_int, metadata_list.split(', '))

        spents_list = entry.metadata.get('spent-times', None)
        if spents_list is None:
            spents_list = [None for i in metadata_list]
        else:
            spents_list = map(_int, spents_list.split(', '))

        return zip(metadata_list, spents_list)

    def _gnome_apps(self):
        croplog = CropLog('/home/olpc/.olpc-gnome-stats', gnome_crop,
                          self._start, self._end)
        return croplog.collect()

    def _sessions(self):
        croplog = CropLog('/home/olpc/.olpc-launch-stats', session_crop,
                          self._start, self._end)
        return croplog.collect()

    def _connectivity(self):
        croplog = CropLog('/home/olpc/.olpc-connectivity', connectivity_crop,
                          self._start, self._end)
        return croplog.collect()


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
