#!/usr/bin/env python
import os
import json
import bisect

from connectivitycrop import connectivity_crop

def activities_crop(lines):
    partial = gnome_crop(lines)
    result = {}
    for time, duration, count, bundle_id in partial:
        result[bundle_id] = [[time, duration, count]]
    return result


def gnome_crop(lines):
    durations = {}
    timestamps = {}

    def parse_line(line):
        split = line.split(' ')

        time, description = float(split[0]), split[1]

        app = None
        if len(split) > 2:
            app_id = split[2]
            app_name = ' '.join(split[3:])
            app = (app_id, app_name)

        return time, description, app

    previous = None
    for line in lines:
        if ' ' not in line:
            continue

        time, description, app = parse_line(line)

        if previous is not None:
            durations[previous['app']] += time - previous['time']

        if description == 'ACTIVATE':
            assert app is not None
            if app not in timestamps.keys():
                timestamps[app] = int(time)
                durations[app] = 0

            previous = {'app': app, 'time': time}

        elif description == 'DEACTIVATE':
            previous = None

    partial_result = {}
    for app, duration in durations.items():
        time = timestamps[app]
        duration = int(duration)
        app_name = app[1]

        if app_name not in partial_result.keys():
            partial_result[app_name] = [time, duration, 1]
        else:
            prev_time, prev_duration, prev_count = partial_result[app_name]
            new_time = min(time, prev_time)
            new_duration = prev_duration + duration
            new_count = prev_count + 1
            partial_result[app_name] = [new_time, new_duration, new_count]

    result = []
    for app_name, data in partial_result.items():
        result.append(data + [app_name])

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
            if cur_data is None:
                continue

            cur_data[1] = int(time) - cur_data[0]
            data.append(cur_data)
            cur_data = None

    return data


def keep_session_log(lines):
    return len(lines) > 0 and 'START' in lines[-1]

def clean_log(log_path, keep_last_line, line=None):
    log_file = open(log_path, 'w')
    if keep_last_line:
        log_file.write(line + '\n')
    log_file.close()

class CropLog(object):
    def __init__(self, filename, crop_method, start=None, end=None):
        self._filename = filename
        self._crop_method = crop_method
        self._start = start
        self._end = end
        self._data = None

    def collect(self):
        if self._data is None:
            try:
                with open(self._filename) as f:
                    alist = [line.rstrip() for line in f]
                    self._data = self._crop_method(alist)
            except IOError:
                return []

        return self._data


__test__ = dict(allem="""

>>> crop = CropLog('croplog_test_session.data', session_crop)
>>> crop.collect()
[[1394741547, 3, True], [1394741587, None, False], [1394741626, 3, True]]

>>> crop = CropLog('croplog_test_sugar.data', activities_crop)
>>> list(sorted(crop.collect().items()))
[('edu.mit.media.ScratchActivity', [[1405625079, 19, 1]]), ('org.laptop.JournalActivity', [[1405625058, 2, 1]]), ('org.laptop.Oficina', [[1405625023, 33, 1]]), ('tv.alterna.Clock', [[1405625054, 8, 1]])]

[[1405084404, 35, 1, 'gcalctool'], [1405084398, 17, 1, 'Firefox'], [1405084453, 14, 1, 'gedit']]

>>> crop = CropLog('croplog_test_gnome.data', gnome_crop)
>>> crop.collect()
[[1405084404, 35, 1, 'gcalctool'], [1405084398, 17, 1, 'Firefox'], [1405084453, 14, 1, 'gedit']]

>>> crop = CropLog('croplog_test_gnome2.data', gnome_crop)
>>> crop.collect()
[[1405099608, 26, 2, 'gcalctool']]

>>> crop = CropLog('unexistent_file.data', session_crop)
>>> crop.collect()
[]

>>> crop = CropLog('croplog_test_connectivity.data', connectivity_crop)
>>> data = crop.collect()
>>> len(data)
2

>>> data[0]
[1400512014, '4C:72:B9:3C:4B:D3', -57.0, 65.0, 6, 2.412, 24279, 5980, 11360528, 2481986]

>>> data[1]
[1400515615, '4C:72:B9:3C:4B:D3', -55.5, 65.0, 13, 2.412, 18164, 6410, 11980015, 3039494]

>>> with open('croplog_test_session.data') as f:
...     alist = [line.rstrip() for line in f]
...     keep_session_log(alist)
True

>>> with open('croplog_test_session2.data') as f:
...     alist = [line.rstrip() for line in f]
...     keep_session_log(alist)
False

""")

if __name__ == '__main__':
    import doctest
    doctest.testmod()
