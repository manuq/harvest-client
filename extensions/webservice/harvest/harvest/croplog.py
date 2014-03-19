#!/usr/bin/env python
import os
import json
import bisect

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

>>> lines = "1394741547 START_SUGAR\\n" + \\
...         "1394741550 END\\n" + \\
...         "1394741587 START_GNOME\\n" + \\
...         "1394741626 START_SUGAR\\n" + \\
...         "1394741629 END\\n" + \\
...         "1394741683 START_SUGAR\\n"

>>> session_crop(lines.split('\\n'))
[[1394741547, 3, True], [1394741587, None, False], [1394741626, 3, True], [1394741683, None, True]]

>>> json.dumps(session_crop(lines.split('\\n')))
'[[1394741547, 3, true], [1394741587, null, false], [1394741626, 3, true], [1394741683, null, true]]'

>>> crop = CropLog('croplog_test.data', session_crop)
>>> crop.collect()
[[1394741547, 3, True], [1394741587, None, False], [1394741626, 3, True], [1394741683, None, True]]

""")

if __name__ == '__main__':
    import doctest
    doctest.testmod()
