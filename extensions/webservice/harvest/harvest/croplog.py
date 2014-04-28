#!/usr/bin/env python
import os
import json
import bisect

def gnome_crop(lines):
    data = {}
    partials = {}
    timestamps = {}

    for line in lines:
        if ' ' not in line:
            continue

        split = line.split(' ')
        time, description = float(split[0]), split[1]
        app_name = ' '.join(split[2:])

        if description == 'START':
            timestamps[app_name] = int(time)

        if description not in ('ACTIVATE', 'DEACTIVATE'):
            continue

        if app_name not in data.keys():
            data[app_name] = 0

        if description == 'ACTIVATE':
            partials[app_name] = time
        else:
            duration = time - partials[app_name]
            data[app_name] += duration

    result = []
    for app_name, duration in data.items():
        name = ' '.join(app_name.split(' ')[1:])
        result.append([timestamps[app_name], int(duration), name])
    return result

def session_crop(lines):
    data = []
    cur_data = None
    for line in lines:
        if ' ' not in line:
            continue

        time, description = line.split(' ')
        if description in ('START_SUGAR', 'START_GNOME'):
            if cur_data is not None:
                data.append(cur_data)
                cur_data = None

            cur_data = [int(time), None, description == 'START_SUGAR']

        elif description == 'END':
            cur_data[1] = int(time) - cur_data[0]
            data.append(cur_data)
            cur_data = None

    if cur_data is not None:
        data.append(cur_data)

    return data


class CropLog(object):
    def __init__(self, filename, crop_method, start=None, end=None):
        self._filename = filename
        self._crop_method = crop_method
        self._start = start
        self._end = end
        self._data = None

    def collect(self):
        if self._data is None:
            with open(self._filename) as f:
                alist = [line.rstrip() for line in f]
                self._data = self._crop_method(alist)

        return self._data


__test__ = dict(allem="""

>>> crop = CropLog('croplog_test_session.data', session_crop)
>>> crop.collect()
[[1394741547, 3, True], [1394741587, None, False], [1394741626, 3, True], [1394741683, None, True]]

>>> crop = CropLog('croplog_test_gnome.data', gnome_crop)
>>> crop.collect()
[[1400501023, 9, 'Terminal'], [1400501033, 47, 'inkscape'], [1400501069, 25, 'inkscape']]

""")

if __name__ == '__main__':
    import doctest
    doctest.testmod()