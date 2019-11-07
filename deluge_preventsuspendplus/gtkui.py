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

from __future__ import division, unicode_literals

import logging

from gi.repository import Gtk

import deluge.component as component
from deluge.plugins.pluginbase import Gtk3PluginBase
from deluge.ui.client import client

from .common import get_resource

log = logging.getLogger(__name__)


class GtkUI(Gtk3PluginBase):
    def enable(self):
        self.builder = Gtk.Builder.new_from_file(get_resource('config.ui'))
        self.builder.get_object('chk_enable').connect('toggled', self._on_enabled_toggled)

        component.get('Preferences').add_page('Prevent Suspend Plus', self.builder.get_object('prefs_box'))
        plugin_manager = component.get('PluginManager')
        plugin_manager.register_hook('on_apply_prefs', self.on_apply_prefs)
        plugin_manager.register_hook('on_show_prefs', self.on_show_prefs)
        self.on_show_prefs()

    def disable(self):
        component.get('Preferences').remove_page('Prevent Suspend Plus')
        plugin_manager = component.get('PluginManager')
        plugin_manager.deregister_hook('on_apply_prefs', self.on_apply_prefs)
        plugin_manager.deregister_hook('on_show_prefs', self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug('Applying prefs for PreventSuspendPlus')
        config = {}
        config['enabled'] = self.builder.get_object('chk_enable').get_active()
        config['prevent_when'] = self.builder.get_object('combo_prevent_when').get_active()
        client.preventsuspendplus.set_config(config)

    def on_show_prefs(self):
        client.preventsuspendplus.get_config().addCallback(self._on_get_config)

    def _on_get_config(self, config):
        log.debug('Config: %s', config)
        self.builder.get_object('chk_enable').set_active(config['enabled'])
        prevent_when = self.builder.get_object('combo_prevent_when')
        prevent_when.set_active(config['prevent_when'])
        prevent_when.set_sensitive(config['enabled'])

    def _on_enabled_toggled(self, widget, data=None):
        prevent_when = self.builder.get_object('combo_prevent_when')
        prevent_when.set_sensitive(widget.get_active())
