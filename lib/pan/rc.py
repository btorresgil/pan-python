#
# Copyright (c) 2013 Kevin Steves <kevin.steves@pobox.com>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

import logging
import sys
import os
import re
import pprint

# Create a module logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

_search_path = ['__init__()', '.', '~']
_filename = '.panrc'
_valid_varnames = set([
    'hostname',
    'port',
    'serial',
    'api_username',
    'api_password',
    'api_key',
    ])

_indent = 2


class PanRcError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class PanRc:
    def __init__(self,
                 tag=None,
                 init_panrc=None,
                 search_path=_search_path,
                 filename=_filename):
        self.tag = tag
        self.init_panrc = init_panrc
        self.search_path = search_path
        self.filename = filename
        self.panrc = {}

        if self.tag is not None:
            regexp = r'^[\w-]+$'
            if re.search(regexp, self.tag) is None:
                raise PanRcError('tag must match regexp "%s"' % regexp)

        self.__parse_path()
        s = pprint.pformat(self.panrc, indent=_indent)
        logger.debug('panrc: %s' % (s,))

    def __parse_path(self):
        panrcs = []

        for basename in self.search_path:
            if basename == '__init__()':
                if self.init_panrc:
                    s = pprint.pformat(self.init_panrc,
                                       indent=_indent)
                    logger.debug2('__parse_path: __init__(): %s' % (s,))
                    panrcs.append(self.init_panrc)
            else:
                path = os.path.expanduser(basename)  # ~, ~user
                path = os.path.expandvars(path)      # $FOO
                path = os.path.join(path, self.filename)
                d = self.__parse_file(path)
                if d:
                    s = pprint.pformat(d, indent=_indent)
                    logger.debug2('__parse_path: %s: %s' % (path, s))
                    panrcs.append(d)

        if panrcs:
            self.__merge_panrcs(panrcs)

    def __parse_file(self, path):
        try:
            f = open(path, 'r')
        except IOError as msg:
            logger.debug3('open %s: %s' % (path, msg))
            return None

        panrc = {}
        for line in f:
            line = line.rstrip('\r\n')
            if re.search(r'(^#|^\s*$)', line):
                continue
            if self.tag:
                result = re.search(r'\s*(\w+)%([\w-]+)\s*=\s*(.+)', line)
                if (result and result.group(2) == self.tag and
                        result.group(1) in _valid_varnames):
                    panrc[result.group(1)] = result.group(3)
            else:
                result = re.search(r'\s*(\w+)\s*=\s*(.+)', line)
                if (result and result.group(1) in _valid_varnames):
                    panrc[result.group(1)] = result.group(2)

        f.close()

        return panrc

    def __merge_panrcs(self, panrcs):
        panrcs.reverse()
        s = pprint.pformat(panrcs, indent=_indent)
        logger.debug2('panrcs:', (s,))

        for panrc in panrcs:
            for key in panrc.keys():
                self.panrc[key] = panrc[key]

if __name__ == '__main__':
    # python rc.py [tag] [0-3]
    import pan.rc

    tag = None
    debug = 0
    if len(sys.argv) > 1 and sys.argv[1]:
        tag = sys.argv[1]
    if len(sys.argv) > 2 and int(sys.argv[2]):
        debug = int(sys.argv[2])
    # map the debug argument to the logging level
    if debug == 0: debug = logging.INFO
    elif debug == 1: debug = logging.DEBUG
    elif debug == 2: debug = 9  # DEBUG2
    elif debug == 3: debug = 8  # DEBUG3

    # set up logging to stdout
    rootLogger = logging.getLogger()
    rootLogger.setLevel(debug)
    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setLevel(debug)
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    streamHandler.setFormatter(formatter)
    rootLogger.addHandler(streamHandler)

    try:
        rc = pan.rc.PanRc(tag=tag)
    except PanRcError as msg:
        rootLogger.error('pan.rc.PanRc: %s' % (msg,))
        sys.exit(1)
    if not debug:
        rootLogger.info('panrc: %s' %
                        (pprint.pformat(rc.panrc, indent=_indent),))
