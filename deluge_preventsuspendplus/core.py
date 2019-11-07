# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 h3llrais3r <pooh_beer_1@hotmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

from twisted.internet.defer import Deferred
from twisted.internet.task import LoopingCall

import deluge.component as component
import deluge.configmanager
from deluge.common import windows_check
from deluge.core.rpcserver import export
from deluge.plugins.pluginbase import CorePluginBase

log = logging.getLogger(__name__)

DEFAULT_PREFS = {
    'enabled': True,
    'prevent_when': 1
}

APPNAME = 'Deluge'
REASON = 'Downloading torrents'


def check_state(states):
    """Return true if at least one of the torrents is in one of the states in states[]"""
    def on_torrents_status(torrent_statuses):
        in_states = False
        for torrent_id, status in torrent_statuses.items():
            if status['state'] in states:
                in_states = True
                break
        return in_states

    d = component.get('Core').get_torrents_status(None, ['state']).addCallback(on_torrents_status)
    return d


def is_downloading():
    """Checks if at least one torrent is downloading"""
    def on_check_state(result):
        return result

    d = check_state(['Downloading'])
    d.addCallback(on_check_state)
    return d


def is_downloading_or_seeding():
    """Checks if at least one torrent is downloading or seeding"""
    def on_check_state(result):
        return result

    d = check_state(['Downloading', 'Seeding'])
    d.addCallback(on_check_state)
    return d


class DBusInhibitor:
    def __init__(self, name, path, interface, method=['Inhibit', 'UnInhibit']):
        self.name = name
        self.path = path
        self.interface_name = interface

        import dbus
        bus = dbus.SessionBus()
        devobj = bus.get_object(self.name, self.path)
        self.iface = dbus.Interface(devobj, self.interface_name)
        # Check we have the right attributes
        self._inhibit = getattr(self.iface, method[0])
        self._uninhibit = getattr(self.iface, method[1])

    def inhibit(self):
        log.info('Inhibit (prevent) suspend mode')
        self.cookie = self._inhibit(APPNAME, REASON)

    def uninhibit(self):
        log.info('Uninhibit (allow) suspend mode')
        self._uninhibit(self.cookie)


class GnomeSessionInhibitor(DBusInhibitor):
    TOPLEVEL_XID = 0
    INHIBIT_SUSPEND = 4

    def __init__(self):
        DBusInhibitor.__init__(self, 'org.gnome.SessionManager',
                               '/org/gnome/SessionManager',
                               'org.gnome.SessionManager',
                               ['Inhibit', 'Uninhibit'])

    def inhibit(self):
        log.info('Inhibit (prevent) suspend mode')
        self.cookie = self._inhibit(APPNAME,
                                    GnomeSessionInhibitor.TOPLEVEL_XID,
                                    REASON,
                                    GnomeSessionInhibitor.INHIBIT_SUSPEND)


class WindowsInhibitor:
    """https://msdn.microsoft.com/en-us/library/windows/desktop/aa373208(v=vs.85).aspx"""
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

    def __init__(self):
        pass

    def inhibit(self):
        import ctypes
        log.info('Inhibit (prevent) suspend mode')
        ctypes.windll.kernel32.SetThreadExecutionState(
            WindowsInhibitor.ES_CONTINUOUS | WindowsInhibitor.ES_SYSTEM_REQUIRED)

    def uninhibit(self):
        import ctypes
        log.info('Uninhibit (allow) suspend mode')
        ctypes.windll.kernel32.SetThreadExecutionState(WindowsInhibitor.ES_CONTINUOUS)


class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager('preventsuspendplus.conf', DEFAULT_PREFS)

        self.inhibited = False
        self.update_timer = None
        self.inhibitor = self._get_inhibitor()

        self.update()

    def disable(self):
        self.stop_timer()

        if self.inhibitor is not None:
            if self.inhibited:
                self.inhibitor.uninhibit()
            del self.inhibitor
            self.inhibitor = None

        self.config.save()

    def start_timer(self):
        if self.update_timer is None:
            self.update_timer = LoopingCall(self.update)
            self.update_timer.start(10)

    def stop_timer(self):
        if self.update_timer is not None:
            self.update_timer.stop()
            self.update_timer = None

    def update(self):
        def on_should_inhibit(result):
            if result:
                if not self.inhibited:
                    self.inhibitor.inhibit()
                    self.inhibited = True
            else:
                if self.inhibited:
                    self.inhibitor.uninhibit()
                    self.inhibited = False

        if self.inhibitor is None:
            return False

        if self.config['enabled']:
            self.start_timer()
            d = self.should_inhibit()
            d.addCallback(on_should_inhibit)
        else:
            self.stop_timer()
            if self.inhibited:
                self.inhibitor.uninhibit()
                self.inhibited = False

        return True

    def should_inhibit(self):
        def on_state_check(result):
            return result

        d = None
        if self.config['prevent_when'] == 0:
            d = is_downloading()
        elif self.config['prevent_when'] == 1:
            d = is_downloading_or_seeding()
        elif self.config['prevent_when'] == 2:
            d = Deferred()
            d.callback(True)  # Always inhibit
        d.addCallback(on_state_check)
        return d

    def _get_inhibitor(self):
        if windows_check():
            try:
                log.debug('Creating Windows inhibitor')
                return WindowsInhibitor()
            except Exception as e:
                log.debug('Could not initialise the Windows inhibitor: %s' % e)
        else:
            try:
                log.debug('Creating Gnome session inhibitor')
                return GnomeSessionInhibitor()
            except Exception as e:
                log.debug('Could not initialise the Gnome session inhibitor: %s' % e)

            try:
                log.debug('Creating Freedesktop inhibitor')
                return DBusInhibitor('org.freedesktop.PowerManagement',
                                     '/org/freedesktop/PowerManagement/Inhibit',
                                     'org.freedesktop.PowerManagement.Inhibit')
            except Exception as e:
                log.debug('Could not initialise the Freedesktop inhibitor: %s' % e)

            try:
                log.debug('Creating Gnome inhibitor')
                return DBusInhibitor('org.gnome.PowerManager',
                                     '/org/gnome/PowerManager',
                                     'org.gnome.PowerManager')
            except Exception as e:
                log.debug('Could not initialise the gnome inhibitor: %s' % e)

        log.error('Could not initialize any inhibitor')
        return None

    @export
    def get_config(self):
        """Get all the preferences as a dictionary"""
        out = self.config.config
        # Set indication if we can inhibit (if an inhibitor is available)
        out['_can_inhibit'] = self.inhibitor is not None
        return out

    @export
    def set_config(self, config):
        """Set the config with values from dictionary"""
        for key in config:
            self.config[key] = config[key]

        # Save the config and update accordingly
        self.config.save()
        self.update()
