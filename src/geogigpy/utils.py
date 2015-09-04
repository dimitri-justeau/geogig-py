# coding: utf-8

import os
import datetime
import time


def mkdir(newdir):
    newdir = newdir.strip('\n\r ')
    if os.path.isdir(newdir):
        pass
    else:
        (head, tail) = os.path.split(newdir)
        if head and not os.path.isdir(head):
            mkdir(head)
        if tail:
            os.mkdir(newdir)


def prettydate(d):
    """Formats a utc date"""
    diff = datetime.datetime.utcnow() - d
    s = ''
    secs = diff.seconds
    if diff.days == 1:
        s = "1 day ago"
    elif diff.days > 1:
        s = "{} days ago".format(int(diff.days))
    elif secs < 120:
        s = "1 minute ago"
    elif secs < 3600:
        s = "{} minutes ago".format(int(secs/60))
    elif secs < 7200:
        s = "1 hour ago"
    else:
        s = '{} hours ago'.format(int(secs/3600))

    epoch = time.mktime(d.timetuple())
    t1 = datetime.datetime.fromtimestamp(epoch)
    t2 = datetime.datetime.utcfromtimestamp(epoch)
    offset = t1 - t2
    local = d + offset
    s += local.strftime(' [%x %H:%M]')
    return s
