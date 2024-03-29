# -*- coding: utf-8 -*-
# vim: autoindent shiftwidth=4 expandtab textwidth=120 tabstop=4 softtabstop=4

###############################################################################
# OpenLP - Open Source Lyrics Projection                                      #
# --------------------------------------------------------------------------- #
# Copyright (c) 2008-2013 Raoul Snyman                                        #
# Portions copyright (c) 2008-2013 Tim Bentley, Gerald Britton, Jonathan      #
# Corwin, Samuel Findlay, Michael Gorven, Scott Guerrieri, Matthias Hub,      #
# Meinert Jordan, Armin Köhler, Erik Lundin, Edwin Lunando, Brian T. Meyer.   #
# Joshua Miller, Stevan Pettit, Andreas Preikschat, Mattias Põldaru,          #
# Christian Richter, Philip Ridout, Simon Scudder, Jeffrey Smith,             #
# Maikel Stuivenberg, Martin Thompson, Jon Tibble, Dave Warnock,              #
# Frode Woldsund, Martin Zibricky, Patrick Zimmermann                         #
# --------------------------------------------------------------------------- #
# This program is free software; you can redistribute it and/or modify it     #
# under the terms of the GNU General Public License as published by the Free  #
# Software Foundation; version 2 of the License.                              #
#                                                                             #
# This program is distributed in the hope that it will be useful, but WITHOUT #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or       #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for    #
# more details.                                                               #
#                                                                             #
# You should have received a copy of the GNU General Public License along     #
# with this program; if not, write to the Free Software Foundation, Inc., 59  #
# Temple Place, Suite 330, Boston, MA 02111-1307 USA                          #
###############################################################################

import logging

from PyQt4 import QtGui

from openlp.core.lib import Plugin, StringContent, translate, build_icon
from openlp.plugins.remotes.lib import RemoteTab, HttpServer

log = logging.getLogger(__name__)

__default_settings__ = {
        'remotes/twelve hour': True,
        'remotes/port': 4316,
        'remotes/https port': 4317,
        'remotes/https enabled': False,
        'remotes/user id': 'openlp',
        'remotes/password': 'password',
        'remotes/authentication enabled': False,
        'remotes/ip address': '0.0.0.0'
}


class RemotesPlugin(Plugin):
    log.info('Remote Plugin loaded')

    def __init__(self):
        """
        remotes constructor
        """
        super(RemotesPlugin, self).__init__('remotes', __default_settings__, settings_tab_class=RemoteTab)
        self.icon_path = ':/plugins/plugin_remote.png'
        self.icon = build_icon(self.icon_path)
        self.weight = -1
        self.server = None

    def initialise(self):
        """
        Initialise the remotes plugin, and start the http server
        """
        log.debug('initialise')
        super(RemotesPlugin, self).initialise()
        self.server = HttpServer()
        self.server.start_server()

    def finalise(self):
        """
        Tidy up and close down the http server
        """
        log.debug('finalise')
        super(RemotesPlugin, self).finalise()
        if self.server:
            self.server.close()
            self.server = None

    def about(self):
        """
        Information about this plugin
        """
        about_text = translate('RemotePlugin', '<strong>Remote Plugin</strong>'
            '<br />The remote plugin provides the ability to send messages to '
            'a running version of OpenLP on a different computer via a web '
            'browser or through the remote API.')
        return about_text

    def set_plugin_text_strings(self):
        """
        Called to define all translatable texts of the plugin
        """
        ## Name PluginList ##
        self.text_strings[StringContent.Name] = {
            'singular': translate('RemotePlugin', 'Remote', 'name singular'),
            'plural': translate('RemotePlugin', 'Remotes', 'name plural')
        }
        ## Name for MediaDockManager, SettingsManager ##
        self.text_strings[StringContent.VisibleName] = {
            'title': translate('RemotePlugin', 'Remote', 'container title')
        }

    def config_update(self):
        """
        Called when Config is changed to restart the server on new address or port
        """
        log.debug('remote config changed')
        self.main_window.information_message(translate('RemotePlugin', 'Configuration Change'),
            translate('RemotePlugin', 'OpenLP will need to be restarted for the Remote changes to become active.'))
