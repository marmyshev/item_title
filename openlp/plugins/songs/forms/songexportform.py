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
"""
The :mod:`songexportform` module provides the wizard for exporting songs to the
OpenLyrics format.
"""
import logging

from PyQt4 import QtCore, QtGui

from openlp.core.lib import Registry, UiStrings, create_separated_list, build_icon, translate
from openlp.core.lib.ui import critical_error_message_box
from openlp.core.ui.wizard import OpenLPWizard, WizardStrings
from openlp.plugins.songs.lib.db import Song
from openlp.plugins.songs.lib.openlyricsexport import OpenLyricsExport

log = logging.getLogger(__name__)


class SongExportForm(OpenLPWizard):
    """
    This is the Song Export Wizard, which allows easy exporting of Songs to the
    OpenLyrics format.
    """
    log.info('SongExportForm loaded')

    def __init__(self, parent, plugin):
        """
        Instantiate the wizard, and run any extra setup we need to.

        ``parent``
            The QWidget-derived parent of the wizard.

        ``plugin``
            The songs plugin.
        """
        super(SongExportForm, self).__init__(parent, plugin, 'song_export_wizard', ':/wizards/wizard_exportsong.bmp')
        self.stop_export_flag = False
        Registry().register_function('openlp_stop_wizard', self.stop_export)

    def stop_export(self):
        """
        Sets the flag for the exporter to stop the export.
        """
        log.debug('Stopping songs export')
        self.stop_export_flag = True

    def setupUi(self, image):
        """
        Set up the song wizard UI.
        """
        super(SongExportForm, self).setupUi(image)

    def custom_signals(self):
        """
        Song wizard specific signals.
        """
        self.availableListWidget.itemActivated.connect(self.onItemActivated)
        self.searchLineEdit.textEdited.connect(self.onSearchLineEditChanged)
        self.uncheckButton.clicked.connect(self.onUncheckButtonClicked)
        self.checkButton.clicked.connect(self.onCheckButtonClicked)
        self.directoryButton.clicked.connect(self.onDirectoryButtonClicked)

    def add_custom_pages(self):
        """
        Add song wizard specific pages.
        """
        # The page with all available songs.
        self.availableSongsPage = QtGui.QWizardPage()
        self.availableSongsPage.setObjectName('availableSongsPage')
        self.availableSongsLayout = QtGui.QHBoxLayout(self.availableSongsPage)
        self.availableSongsLayout.setObjectName('availableSongsLayout')
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName('verticalLayout')
        self.availableListWidget = QtGui.QListWidget(self.availableSongsPage)
        self.availableListWidget.setObjectName('availableListWidget')
        self.verticalLayout.addWidget(self.availableListWidget)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName('horizontalLayout')
        self.searchLabel = QtGui.QLabel(self.availableSongsPage)
        self.searchLabel.setObjectName('searchLabel')
        self.horizontalLayout.addWidget(self.searchLabel)
        self.searchLineEdit = QtGui.QLineEdit(self.availableSongsPage)
        self.searchLineEdit.setObjectName('searchLineEdit')
        self.horizontalLayout.addWidget(self.searchLineEdit)
        spacer_item = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacer_item)
        self.uncheckButton = QtGui.QPushButton(self.availableSongsPage)
        self.uncheckButton.setObjectName('uncheckButton')
        self.horizontalLayout.addWidget(self.uncheckButton)
        self.checkButton = QtGui.QPushButton(self.availableSongsPage)
        self.checkButton.setObjectName('selectButton')
        self.horizontalLayout.addWidget(self.checkButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.availableSongsLayout.addLayout(self.verticalLayout)
        self.addPage(self.availableSongsPage)
        # The page with the selected songs.
        self.exportSongPage = QtGui.QWizardPage()
        self.exportSongPage.setObjectName('availableSongsPage')
        self.exportSongLayout = QtGui.QHBoxLayout(self.exportSongPage)
        self.exportSongLayout.setObjectName('exportSongLayout')
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName('gridLayout')
        self.selectedListWidget = QtGui.QListWidget(self.exportSongPage)
        self.selectedListWidget.setObjectName('selectedListWidget')
        self.gridLayout.addWidget(self.selectedListWidget, 1, 0, 1, 1)
        # FIXME: self.horizontalLayout is already defined above?!?!?
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName('horizontalLayout')
        self.directoryLabel = QtGui.QLabel(self.exportSongPage)
        self.directoryLabel.setObjectName('directoryLabel')
        self.horizontalLayout.addWidget(self.directoryLabel)
        self.directoryLineEdit = QtGui.QLineEdit(self.exportSongPage)
        self.directoryLineEdit.setObjectName('directoryLineEdit')
        self.horizontalLayout.addWidget(self.directoryLineEdit)
        self.directoryButton = QtGui.QToolButton(self.exportSongPage)
        self.directoryButton.setIcon(build_icon(':/exports/export_load.png'))
        self.directoryButton.setObjectName('directoryButton')
        self.horizontalLayout.addWidget(self.directoryButton)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.exportSongLayout.addLayout(self.gridLayout)
        self.addPage(self.exportSongPage)

    def retranslateUi(self):
        """
        Song wizard localisation.
        """
        self.setWindowTitle(translate('SongsPlugin.ExportWizardForm', 'Song Export Wizard'))
        self.title_label.setText(WizardStrings.HeaderStyle %
            translate('OpenLP.Ui', 'Welcome to the Song Export Wizard'))
        self.information_label.setText(translate('SongsPlugin.ExportWizardForm', 'This wizard will help to'
            ' export your songs to the open and free <strong>OpenLyrics </strong> worship song format.'))
        self.availableSongsPage.setTitle(translate('SongsPlugin.ExportWizardForm', 'Select Songs'))
        self.availableSongsPage.setSubTitle(translate('SongsPlugin.ExportWizardForm',
            'Check the songs you want to export.'))
        self.searchLabel.setText('%s:' % UiStrings().Search)
        self.uncheckButton.setText(translate('SongsPlugin.ExportWizardForm', 'Uncheck All'))
        self.checkButton.setText(translate('SongsPlugin.ExportWizardForm', 'Check All'))
        self.exportSongPage.setTitle(translate('SongsPlugin.ExportWizardForm', 'Select Directory'))
        self.exportSongPage.setSubTitle(translate('SongsPlugin.ExportWizardForm',
            'Select the directory where you want the songs to be saved.'))
        self.directoryLabel.setText(translate('SongsPlugin.ExportWizardForm', 'Directory:'))
        self.progress_page.setTitle(translate('SongsPlugin.ExportWizardForm', 'Exporting'))
        self.progress_page.setSubTitle(translate('SongsPlugin.ExportWizardForm',
            'Please wait while your songs are exported.'))
        self.progress_label.setText(WizardStrings.Ready)
        self.progress_bar.setFormat(WizardStrings.PercentSymbolFormat)

    def validateCurrentPage(self):
        """
        Validate the current page before moving on to the next page.
        """
        if self.currentPage() == self.welcome_page:
            return True
        elif self.currentPage() == self.availableSongsPage:
            items = [
                item for item in self._findListWidgetItems(
                self.availableListWidget) if item.checkState()
            ]
            if not items:
                critical_error_message_box(UiStrings().NISp,
                    translate('SongsPlugin.ExportWizardForm', 'You need to add at least one Song to export.'))
                return False
            self.selectedListWidget.clear()
            # Add the songs to the list of selected songs.
            for item in items:
                song = QtGui.QListWidgetItem(item.text())
                song.setData(QtCore.Qt.UserRole, item.data(QtCore.Qt.UserRole))
                song.setFlags(QtCore.Qt.ItemIsEnabled)
                self.selectedListWidget.addItem(song)
            return True
        elif self.currentPage() == self.exportSongPage:
            if not self.directoryLineEdit.text():
                critical_error_message_box(
                    translate('SongsPlugin.ExportWizardForm', 'No Save Location specified'),
                    translate('SongsPlugin.ExportWizardForm', 'You need to specify a directory.'))
                return False
            return True
        elif self.currentPage() == self.progress_page:
            self.availableListWidget.clear()
            self.selectedListWidget.clear()
            return True

    def setDefaults(self):
        """
        Set default form values for the song export wizard.
        """
        self.restart()
        self.finish_button.setVisible(False)
        self.cancel_button.setVisible(True)
        self.availableListWidget.clear()
        self.selectedListWidget.clear()
        self.directoryLineEdit.clear()
        self.searchLineEdit.clear()
        # Load the list of songs.
        self.application.set_busy_cursor()
        songs = self.plugin.manager.get_all_objects(Song)
        songs.sort(key=lambda song: song.sort_key)
        for song in songs:
            # No need to export temporary songs.
            if song.temporary:
                continue
            authors = create_separated_list([author.display_name for author in song.authors])
            title = '%s (%s)' % (str(song.title), authors)
            item = QtGui.QListWidgetItem(title)
            item.setData(QtCore.Qt.UserRole, song)
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.availableListWidget.addItem(item)
        self.application.set_normal_cursor()

    def pre_wizard(self):
        """
        Perform pre export tasks.
        """
        super(SongExportForm, self).pre_wizard()
        self.progress_label.setText(translate('SongsPlugin.ExportWizardForm', 'Starting export...'))
        self.application.process_events()

    def performWizard(self):
        """
        Perform the actual export. This creates an *openlyricsexport* instance
        and calls the *do_export* method.
        """
        songs = [
            song.data(QtCore.Qt.UserRole)
            for song in self._findListWidgetItems(self.selectedListWidget)
        ]
        exporter = OpenLyricsExport(self, songs, self.directoryLineEdit.text())
        if exporter.do_export():
            self.progress_label.setText(translate('SongsPlugin.SongExportForm',
                    'Finished export. To import these files use the <strong>OpenLyrics</strong> importer.'))
        else:
            self.progress_label.setText(translate('SongsPlugin.SongExportForm', 'Your song export failed.'))

    def _findListWidgetItems(self, listWidget, text=''):
        """
        Returns a list of *QListWidgetItem*s of the ``listWidget``. Note, that
        hidden items are included.

        ``listWidget``
            The widget to get all items from. (QListWidget)

        ``text``
            The text to search for. (unicode string)
        """
        return [
            item for item in listWidget.findItems(text, QtCore.Qt.MatchContains)
        ]

    def onItemActivated(self, item):
        """
        Called, when an item in the *availableListWidget* has been triggered.
        The item is check if it was not checked, whereas it is unchecked when it
        was checked.

        ``item``
            The *QListWidgetItem* which was triggered.
        """
        item.setCheckState(
            QtCore.Qt.Unchecked if item.checkState() else QtCore.Qt.Checked)

    def onSearchLineEditChanged(self, text):
        """
        The *searchLineEdit*'s text has been changed. Update the list of
        available songs. Note that any song, which does not match the ``text``
        will be hidden, but not unchecked!

        ``text``
            The text of the *searchLineEdit*.
        """
        search_result = [
            song for song in self._findListWidgetItems(self.availableListWidget, text)
        ]
        for item in self._findListWidgetItems(self.availableListWidget):
            item.setHidden(item not in search_result)

    def onUncheckButtonClicked(self):
        """
        The *uncheckButton* has been clicked. Set all visible songs unchecked.
        """
        for row in range(self.availableListWidget.count()):
            item = self.availableListWidget.item(row)
            if not item.isHidden():
                item.setCheckState(QtCore.Qt.Unchecked)

    def onCheckButtonClicked(self):
        """
        The *checkButton* has been clicked. Set all visible songs checked.
        """
        for row in range(self.availableListWidget.count()):
            item = self.availableListWidget.item(row)
            if not item.isHidden():
                item.setCheckState(QtCore.Qt.Checked)

    def onDirectoryButtonClicked(self):
        """
        Called when the *directoryButton* was clicked. Opens a dialog and writes
        the path to *directoryLineEdit*.
        """
        self.get_folder(translate('SongsPlugin.ExportWizardForm', 'Select Destination Folder'),
            self.directoryLineEdit, 'last directory export')
