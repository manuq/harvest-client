import sys

def group(lst, n):
    """
    >>> group(range(10), 3)
    [(0, 1, 2), (3, 4, 5), (6, 7, 8)]

    >>> group(range(10), 4)
    [(0, 1, 2, 3), (4, 5, 6, 7)]

    """
    return zip(*[lst[i::n] for i in range(n)])


def most_frequent(words):
    """
    >>> most_frequent(['4C:72:B9:3C:4B:D3', '4C:72:B9:3C:4B:D3', '00-B0-D0-86-BB-F7'])
    '4C:72:B9:3C:4B:D3'

    >>> most_frequent(['00-B0-D0-86-BB-F7', '4C:72:B9:3C:4B:D3', '4C:72:B9:3C:4B:D3', '00-B0-D0-86-BB-F7'])
    '00-B0-D0-86-BB-F7'

    """
    frequencies = {}
    for w in words:
        if w not in frequencies:
            frequencies[w] = 0
        else:
            frequencies[w] += 1

    most_frequent = max(frequencies.values())
    for w in words:
        if frequencies[w] == most_frequent:
            return w


def median(numbers):
    """
    >>> median([5, 2, 4, 3, 1])
    3

    >>> median([5, 2, 4, 3, 1, 6])
    3.5

    >>> median([-44, -50, -66, -67, -59, -63, -60])
    -60

    """
    sorts = sorted(numbers)
    length = len(sorts)
    if not length % 2:
        return (sorts[length / 2] + sorts[length / 2 - 1]) / 2.0
    return sorts[length / 2]


def bps(bytes_data, seconds):
    """
    >>> bps(415998466 - 415853561, 300)
    3864

    >>> bps(1, 1)
    8

    """
    return int(bytes_data * 8 / float(seconds))


def connectivity_crop(lines):
    input_data = []
    for line in lines:
        input_data.append(line.split(' '))

    data = []
    data_groups = group(input_data, 12)
    for grp in data_groups:
        ap_common = most_frequent(list(i[1] for i in grp))
        sl_median = median(list(float(i[2]) for i in grp))
        br_median = median(list(float(i[3]) for i in grp))

        paired = zip(list(grp[1:]) + [None], list(grp))

        rxs = []
        txs = []
        for next_line, curr_line in paired:
            if next_line is not None:
                rxs.append(bps(int(next_line[6]) - int(curr_line[6]), 300))
                txs.append(bps(int(next_line[7]) - int(curr_line[7]), 300))

        ret_diff = int(grp[-1][4]) - int(grp[0][4])

        freq = float(grp[0][5])

        rx_median = median(rxs)
        tx_median = median(txs)

        rx_diff = int(grp[-1][6]) - int(grp[0][6])
        tx_diff = int(grp[-1][7]) - int(grp[0][7])

        data.append([ap_common, sl_median, br_median, ret_diff, freq,
                     rx_median, tx_median, rx_diff, tx_diff])

    return data


if __name__ == '__main__':
    import doctest
    doctest.testmod()
