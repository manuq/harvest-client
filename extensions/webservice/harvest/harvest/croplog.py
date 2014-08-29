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
    previous_time = None
    for line in lines:
        if ' ' not in line:
            continue

        time, description = line.split(' ')

        if description in ('START_SUGAR', 'START_GNOME', 'RESUME'):
            previous_time = int(time)

            if description in ('START_SUGAR', 'START_GNOME'):
                if cur_data is not None:
                    data.append(cur_data)
                    cur_data = None

                cur_data = [int(time), None, description == 'START_SUGAR']

        elif description in ('END', 'SUSPEND'):
            if cur_data is None or previous_time is None:
                continue

            if cur_data[1] == None:
                cur_data[1] = 0

            cur_data[1] += int(time) - previous_time

            if description == 'END':
                data.append(cur_data)
                cur_data = None

    return data

def clean_acts_apps_log(log_path, out_path=None):
    if out_path is None:
        out_path = log_path

    keep_lines = []
    with open(log_path, 'r') as log_file:
        lines = [line.rstrip() for line in log_file]
        if ' ACTIVATE' in lines[-1]:
            keep_lines.append(line)

    with open(out_path, 'w') as out_file:
        for line in keep_lines:
            out_file.write(line)

def clean_session_log(log_path, out_path=None):
    if out_path is None:
        out_path = log_path

    keep_lines = []
    with open(log_path, 'r') as log_file:
        lines = [line.rstrip() for line in log_file]
        for line in lines:
            if ' END' in line:
                keep_lines = []
            else:
                keep_lines.append(line)

    with open(out_path, 'w') as out_file:
        for line in keep_lines:
            out_file.write(line + '\n')


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
                    lines = [line.rstrip() for line in f]
                    self._data = self._crop_method(lines)
            except IOError:
                return []

        return self._data


__test__ = dict(allem="""

>>> crop = CropLog('croplog_test_session.data', session_crop)
>>> crop.collect()
[[1394741547, 3, True], [1394741587, None, False], [1394741626, 3, True]]

>>> crop = CropLog('croplog_test_session2.data', session_crop)
>>> crop.collect()
[[1394741547, 3, True], [1394741587, None, False], [1394741626, 3, True]]

>>> crop = CropLog('croplog_test_session3.data', session_crop)
>>> crop.collect()
[[1394741588, 2480, False], [1394762288, None, False], [1394809088, 900, False]]

>>> crop = CropLog('croplog_test_session4.data', session_crop)
>>> crop.collect()
[[1394741588, 2480, False], [1394762288, 4550, False], [1394809088, 900, False]]

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

>>> clean_session_log('croplog_test_session.data', out_path='/tmp/test')
>>> open('/tmp/test').readlines() == open('croplog_test_session_remain.data').readlines()
True

>>> clean_session_log('croplog_test_session2.data', out_path='/tmp/test')
>>> open('/tmp/test').readlines() == []
True

>>> clean_session_log('croplog_test_session5.data', out_path='/tmp/test')
>>> open('/tmp/test').readlines() == open('croplog_test_session5_remain.data').readlines()
True

>>> clean_acts_apps_log('croplog_test_gnome3.data', out_path='/tmp/test')
>>> open('/tmp/test').readlines() == open('croplog_test_gnome3_remain.data').readlines()
True

""")

if __name__ == '__main__':
    import doctest
    doctest.testmod()
