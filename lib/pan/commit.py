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

# Create a module logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

import xml.etree.ElementTree as etree

_valid_part = set([
    'device-and-network-excluded',
    'policy-and-objects-excluded',
    'shared-object-excluded',
    'no-vsys',
    'vsys'])

_part_xml = {
    'device-and-network-excluded':
    '<device-and-network>excluded</device-and-network>',
    'policy-and-objects-excluded':
    '<policy-and-objects>excluded</policy-and-objects>',
    'shared-object-excluded':
    '<shared-object>excluded</shared-object>',
    'no-vsys':
    '<no-vsys></no-vsys>',
    'vsys':
    '<member>%s</member>'}


def valid_part(part):
    return part in _valid_part


class PanCommit:
    def __init__(self,
                 validate=False,
                 force=False,
                 commit_all=False,
                 merge_with_candidate=False):
        self._validate = validate
        self._force = force
        self._commit_all = commit_all
        self._merge_with_candidate = merge_with_candidate
        self.partial = set()
        self._vsys = set()
        self._device = None
        self._device_group = None

    def validate(self):
        self._validate = True

    def force(self):
        self._force = True

    def commit_all(self):
        self._commit_all = True

    def merge_with_candidate(self):
        self._merge_with_candidate = True

    def device_and_network_excluded(self):
        part = 'device-and-network-excluded'
        self.partial.add(part)

    def policy_and_objects_excluded(self):
        part = 'policy-and-objects-excluded'
        self.partial.add(part)

    def shared_object_excluded(self):
        part = 'shared-object-excluded'
        self.partial.add(part)

    def no_vsys(self):
        part = 'no-vsys'
        self.partial.add(part)

    def vsys(self, vsys):
        if not self._commit_all:
            part = 'vsys'
            self.partial.add(part)

        if isinstance(vsys, str):
            vsys = [vsys]
        for name in vsys:
            self._vsys.add(name)

    def device(self, serial):
        self._device = serial

    def device_group(self, device_group):
        self._device_group = device_group

    def cmd(self):
        if self._commit_all:
            return self.__commit_all()
        else:
            return self.__commit()

    def __commit_all(self):
        e = etree.Element("commit-all")
        sp = etree.SubElement(e, "shared-policy")

        if self._device_group:
            dg = etree.SubElement(sp, "device-group")
            n = etree.SubElement(dg, "name")
            n.text = self._device_group

            if self._device:
                d = etree.SubElement(dg, "devices")
                en = etree.SubElement(d, "entry", name=self._device)

        # default when no <merge-with-candidate-cfg/> is 'yes'
        # we default to 'no' like the Web UI
        m = etree.SubElement(sp, "merge-with-candidate-cfg")

        if self._merge_with_candidate:
            m.text = 'yes'
        else:
            m.text = 'no'

        if self._vsys:
            v = etree.SubElement(sp, "vsys")
            v.text = self._vsys.pop()

        logger.debug2('commit-all cmd: %s' % etree.tostring(e))

        return etree.tostring(e)

    def __commit(self):
        s = '<commit>'

        if self._validate:
            s += '<validate>'

        if self._force:
            s += '<force>'

        if self.partial:
            s += '<partial>'
        for part in self.partial:
            if part in _part_xml:
                if part == 'vsys':
                    s += '<vsys>'
                    for name in self._vsys:
                        xml_vsys = _part_xml[part] % name
                        s += xml_vsys
                    s += '</vsys>'
                else:
                    s += _part_xml[part]
        if self.partial:
            s += '</partial>'

        if self._force:
            s += '</force>'

        if self._validate:
            s += '</validate>'

        s += '</commit>'

        logger.debug3('commit cmd:' % s)

        return s
