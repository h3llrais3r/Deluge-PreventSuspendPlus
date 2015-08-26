#
# gtkui.py
#
# Copyright (C) 2015 h3llrais3r <pooh_beer_1@hotmail.com>
# Copyright (C) 2009 Ian Martin <ianmartin@cantab.net>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

import gtk

from deluge import component
from deluge.log import LOG as log
from deluge.plugins.pluginbase import GtkPluginBase
from deluge.ui.client import client

import common


class GtkUI(GtkPluginBase):
    def enable(self):
        self.glade = gtk.glade.XML(common.get_resource("config.glade"))
        self.glade.get_widget("chk_enable").connect("toggled", self._on_enabled_toggled)

        component.get("Preferences").add_page("Prevent Suspend Plus",
                                              self.glade.get_widget("prefs_box"))
        plugin_manager = component.get("PluginManager")
        plugin_manager.register_hook("on_apply_prefs", self.on_apply_prefs)
        plugin_manager.register_hook("on_show_prefs", self.on_show_prefs)
        self.on_show_prefs()

    def disable(self):
        component.get("Preferences").remove_page("Prevent Suspend Plus")
        plugin_manager = component.get("PluginManager")
        plugin_manager.deregister_hook("on_apply_prefs", self.on_apply_prefs)
        plugin_manager.deregister_hook("on_show_prefs", self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug("applying prefs for PreventSuspendPlus")
        config = {"enabled": self.glade.get_widget("chk_enable").get_active(),
                  "prevent_when": self.glade.get_widget("combo_prevent_when").get_active()}
        client.preventsuspendplus.set_config(config)

    def on_show_prefs(self):
        client.preventsuspendplus.get_config().addCallback(self._on_get_config)

    def _on_get_config(self, config):
        """callback for on show_prefs"""
        self.glade.get_widget("chk_enable").set_active(config["enabled"])
        prevent_when = self.glade.get_widget("combo_prevent_when")
        prevent_when.set_active(config["prevent_when"])
        prevent_when.set_sensitive(config["enabled"])

    def _on_enabled_toggled(self, widget, data=None):
        prevent_when = self.glade.get_widget("combo_prevent_when")
        prevent_when.set_sensitive(widget.get_active())
