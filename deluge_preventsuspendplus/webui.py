# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 h3llrais3r <h3llrais3r.github@gmail.com>
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

from deluge.plugins.pluginbase import WebPluginBase

from .common import get_resource

log = logging.getLogger(__name__)


class WebUI(WebPluginBase):

    scripts = [get_resource('preventsuspendplus.js')]
    debug_scripts = scripts
