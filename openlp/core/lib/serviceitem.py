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
The :mod:`serviceitem` provides the service item functionality including the
type and capability of an item.
"""

import cgi
import datetime
import logging
import os
import uuid

from PyQt4 import QtGui

from openlp.core.lib import ImageSource, Settings, Registry, build_icon, clean_tags, expand_tags, translate

log = logging.getLogger(__name__)


class ServiceItemType(object):
    """
    Defines the type of service item
    """
    Text = 1
    Image = 2
    Command = 3


class ItemCapabilities(object):
    """
    Provides an enumeration of a service item's capabilities

    ``CanPreview``
            The capability to allow the ServiceManager to add to the preview tab when making the previous item live.

    ``CanEdit``
            The capability to allow the ServiceManager to allow the item to be edited

    ``CanMaintain``
            The capability to allow the ServiceManager to allow the item to be reordered.

    ``RequiresMedia``
            Determines is the service_item needs a Media Player

    ``CanLoop``
            The capability to allow the SlideController to allow the loop processing.

    ``CanAppend``
            The capability to allow the ServiceManager to add leaves to the
            item

    ``NoLineBreaks``
            The capability to remove lines breaks in the renderer

    ``OnLoadUpdate``
            The capability to update MediaManager when a service Item is loaded.

    ``AddIfNewItem``
            Not Used

    ``ProvidesOwnDisplay``
            The capability to tell the SlideController the service Item has a different display.

    ``HasDetailedTitleDisplay``
            Being Removed and decommissioned.

    ``HasVariableStartTime``
            The capability to tell the ServiceManager that a change to start time is possible.

    ``CanSoftBreak``
            The capability to tell the renderer that Soft Break is allowed

    ``CanWordSplit``
            The capability to tell the renderer that it can split words is
            allowed

    ``HasBackgroundAudio``
            That a audio file is present with the text.

    ``CanAutoStartForLive``
            The capability to ignore the do not play if display blank flag.
    
    ``CanEditTitle``
            The capability to edit the title of the item

    """
    CanPreview = 1
    CanEdit = 2
    CanMaintain = 3
    RequiresMedia = 4
    CanLoop = 5
    CanAppend = 6
    NoLineBreaks = 7
    OnLoadUpdate = 8
    AddIfNewItem = 9
    ProvidesOwnDisplay = 10
    HasDetailedTitleDisplay = 11
    HasVariableStartTime = 12
    CanSoftBreak = 13
    CanWordSplit = 14
    HasBackgroundAudio = 15
    CanAutoStartForLive = 16
    CanEditTitle = 17


class ServiceItem(object):
    """
    The service item is a base class for the plugins to use to interact with
    the service manager, the slide controller, and the projection screen
    compositor.
    """
    log.info('Service Item created')

    def __init__(self, plugin=None):
        """
        Set up the service item.

        ``plugin``
            The plugin that this service item belongs to.
        """
        if plugin:
            self.name = plugin.name
        self.title = ''
        self.processor = None
        self.audit = ''
        self.items = []
        self.iconic_representation = None
        self.raw_footer = []
        self.foot_text = ''
        self.theme = None
        self.service_item_type = None
        self._raw_frames = []
        self._display_frames = []
        self.unique_identifier = 0
        self.notes = ''
        self.from_plugin = False
        self.capabilities = []
        self.is_valid = True
        self.icon = None
        self.themedata = None
        self.main = None
        self.footer = None
        self.bg_image_bytes = None
        self.search_string = ''
        self.data_string = ''
        self.edit_id = None
        self.xml_version = None
        self.start_time = 0
        self.end_time = 0
        self.media_length = 0
        self.from_service = False
        self.image_border = '#000000'
        self.background_audio = []
        self.theme_overwritten = False
        self.temporary_edit = False
        self.auto_play_slides_once = False
        self.auto_play_slides_loop = False
        self.timed_slide_interval = 0
        self.will_auto_start = False
        self.has_original_files = True
        self._new_item()

    def _new_item(self):
        """
        Method to set the internal id of the item. This is used to compare
        service items to see if they are the same.
        """
        self.unique_identifier = str(uuid.uuid1())
        self.validate_item()

    def add_capability(self, capability):
        """
        Add an ItemCapability to a ServiceItem

        ``capability``
            The capability to add
        """
        self.capabilities.append(capability)

    def is_capable(self, capability):
        """
        Tell the caller if a ServiceItem has a capability

        ``capability``
            The capability to test for
        """
        return capability in self.capabilities

    def add_icon(self, icon):
        """
        Add an icon to the service item. This is used when displaying the
        service item in the service manager.

        ``icon``
            A string to an icon in the resources or on disk.
        """
        self.icon = icon
        self.iconic_representation = build_icon(icon)

    def render(self, provides_own_theme_data=False):
        """
        The render method is what generates the frames for the screen and
        obtains the display information from the renderer. At this point all
        slides are built for the given display size.

        ``provides_own_theme_data``
            This switch disables the usage of the item's theme. However, this is
            disabled by default. If this is used, it has to be taken care, that
            the renderer knows the correct theme data. However, this is needed
            for the theme manager.
        """
        log.debug('Render called')
        self._display_frames = []
        self.bg_image_bytes = None
        if not provides_own_theme_data:
            self.renderer.set_item_theme(self.theme)
            self.themedata, self.main, self.footer = self.renderer.pre_render()
        if self.service_item_type == ServiceItemType.Text:
            log.debug('Formatting slides: %s' % self.title)
            # Save rendered pages to this dict. In the case that a slide is used
            # twice we can use the pages saved to the dict instead of rendering
            # them again.
            previous_pages = {}
            for slide in self._raw_frames:
                verse_tag = slide['verseTag']
                if verse_tag in previous_pages and previous_pages[verse_tag][0] == slide['raw_slide']:
                    pages = previous_pages[verse_tag][1]
                else:
                    pages = self.renderer.format_slide(slide['raw_slide'], self)
                    previous_pages[verse_tag] = (slide['raw_slide'], pages)
                for page in pages:
                    page = page.replace('<br>', '{br}')
                    html = expand_tags(cgi.escape(page.rstrip()))
                    self._display_frames.append({
                        'title': clean_tags(page),
                        'text': clean_tags(page.rstrip()),
                        'html': html.replace('&amp;nbsp;', '&nbsp;'),
                        'verseTag': verse_tag
                    })
        elif self.service_item_type == ServiceItemType.Image or self.service_item_type == ServiceItemType.Command:
            pass
        else:
            log.error('Invalid value renderer: %s' % self.service_item_type)
        self.title = clean_tags(self.title)
        # The footer should never be None, but to be compatible with a few
        # nightly builds between 1.9.4 and 1.9.5, we have to correct this to
        # avoid tracebacks.
        if self.raw_footer is None:
            self.raw_footer = []
        self.foot_text = '<br>'.join([_f for _f in self.raw_footer if _f])

    def add_from_image(self, path, title, background=None):
        """
        Add an image slide to the service item.

        ``path``
            The directory in which the image file is located.

        ``title``
            A title for the slide in the service item.
        """
        if background:
            self.image_border = background
        self.service_item_type = ServiceItemType.Image
        self._raw_frames.append({'title': title, 'path': path})
        self.image_manager.add_image(path, ImageSource.ImagePlugin, self.image_border)
        self._new_item()

    def add_from_text(self, raw_slide, verse_tag=None):
        """
        Add a text slide to the service item.

        ``raw_slide``
            The raw text of the slide.
        """
        if verse_tag:
            verse_tag = verse_tag.upper()
        self.service_item_type = ServiceItemType.Text
        title = raw_slide[:30].split('\n')[0]
        self._raw_frames.append({'title': title, 'raw_slide': raw_slide, 'verseTag': verse_tag})
        self._new_item()

    def add_from_command(self, path, file_name, image):
        """
        Add a slide from a command.

        ``path``
            The title of the slide in the service item.

        ``file_name``
            The title of the slide in the service item.

        ``image``
            The command of/for the slide.
        """
        self.service_item_type = ServiceItemType.Command
        self._raw_frames.append({'title': file_name, 'image': image, 'path': path})
        self._new_item()

    def get_service_repr(self, lite_save):
        """
        This method returns some text which can be saved into the service
        file to represent this item.
        """
        service_header = {
            'name': self.name,
            'plugin': self.name,
            'theme': self.theme,
            'title': self.title,
            'icon': self.icon,
            'footer': self.raw_footer,
            'type': self.service_item_type,
            'audit': self.audit,
            'notes': self.notes,
            'from_plugin': self.from_plugin,
            'capabilities': self.capabilities,
            'search': self.search_string,
            'data': self.data_string,
            'xml_version': self.xml_version,
            'auto_play_slides_once': self.auto_play_slides_once,
            'auto_play_slides_loop': self.auto_play_slides_loop,
            'timed_slide_interval': self.timed_slide_interval,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'media_length': self.media_length,
            'background_audio': self.background_audio,
            'theme_overwritten': self.theme_overwritten,
            'will_auto_start': self.will_auto_start,
            'processor': self.processor
        }
        service_data = []
        if self.service_item_type == ServiceItemType.Text:
            service_data = [slide for slide in self._raw_frames]
        elif self.service_item_type == ServiceItemType.Image:
            if lite_save:
                for slide in self._raw_frames:
                    service_data.append({'title': slide['title'], 'path': slide['path']})
            else:
                service_data = [slide['title'] for slide in self._raw_frames]
        elif self.service_item_type == ServiceItemType.Command:
            for slide in self._raw_frames:
                service_data.append({'title': slide['title'], 'image': slide['image'], 'path': slide['path']})
        return {'header': service_header, 'data': service_data}

    def set_from_service(self, serviceitem, path=None):
        """
        This method takes a service item from a saved service file (passed
        from the ServiceManager) and extracts the data actually required.

        ``serviceitem``
            The item to extract data from.

        ``path``
            Defaults to *None*. This is the service manager path for things
            which have their files saved with them or None when the saved
            service is lite and the original file paths need to be preserved..
        """
        log.debug('set_from_service called with path %s' % path)
        header = serviceitem['serviceitem']['header']
        self.title = header['title']
        self.name = header['name']
        self.service_item_type = header['type']
        self.theme = header['theme']
        self.add_icon(header['icon'])
        self.raw_footer = header['footer']
        self.audit = header['audit']
        self.notes = header['notes']
        self.from_plugin = header['from_plugin']
        self.capabilities = header['capabilities']
        # Added later so may not be present in older services.
        self.search_string = header.get('search', '')
        self.data_string = header.get('data', '')
        self.xml_version = header.get('xml_version')
        self.start_time = header.get('start_time', 0)
        self.end_time = header.get('end_time', 0)
        self.media_length = header.get('media_length', 0)
        self.auto_play_slides_once = header.get('auto_play_slides_once', False)
        self.auto_play_slides_loop = header.get('auto_play_slides_loop', False)
        self.timed_slide_interval = header.get('timed_slide_interval', 0)
        self.will_auto_start = header.get('will_auto_start', False)
        self.processor = header.get('processor', None)
        self.has_original_files = True
        #TODO Remove me in 2,3 build phase
        if self.is_capable(ItemCapabilities.HasDetailedTitleDisplay):
            self.capabilities.remove(ItemCapabilities.HasDetailedTitleDisplay)
            self.processor = self.title
            self.title = None
        if 'background_audio' in header:
            self.background_audio = []
            for filename in header['background_audio']:
                # Give them real file paths
                self.background_audio.append(os.path.join(path, filename))
        self.theme_overwritten = header.get('theme_overwritten', False)
        if self.service_item_type == ServiceItemType.Text:
            for slide in serviceitem['serviceitem']['data']:
                self._raw_frames.append(slide)
        elif self.service_item_type == ServiceItemType.Image:
            settings_section = serviceitem['serviceitem']['header']['name']
            background = QtGui.QColor(Settings().value(settings_section + '/background color'))
            if path:
                self.has_original_files = False
                for text_image in serviceitem['serviceitem']['data']:
                    filename = os.path.join(path, text_image)
                    self.add_from_image(filename, text_image, background)
            else:
                for text_image in serviceitem['serviceitem']['data']:
                    self.add_from_image(text_image['path'], text_image['title'], background)
        elif self.service_item_type == ServiceItemType.Command:
            for text_image in serviceitem['serviceitem']['data']:
                if not self.title:
                    self.title = text_image['title']
                if path:
                    self.has_original_files = False
                    self.add_from_command(path, text_image['title'], text_image['image'])
                else:
                    self.add_from_command(text_image['path'], text_image['title'], text_image['image'])
        self._new_item()

    def get_display_title(self):
        """
        Returns the title of the service item.
        """
        if self.is_text() or ItemCapabilities.CanEditTitle in self.capabilities:
            return self.title
        else:
            if len(self._raw_frames) > 1:
                return self.title
            else:
                return self._raw_frames[0]['title']

    def merge(self, other):
        """
        Updates the unique_identifier with the value from the original one
        The unique_identifier is unique for a given service item but this allows one to
        replace an original version.

        ``other``
            The service item to be merged with
        """
        self.unique_identifier = other.unique_identifier
        self.notes = other.notes
        self.temporary_edit = other.temporary_edit
        # Copy theme over if present.
        if other.theme is not None:
            self.theme = other.theme
            self._new_item()
        self.render()
        if self.is_capable(ItemCapabilities.HasBackgroundAudio):
            log.debug(self.background_audio)

    def __eq__(self, other):
        """
        Confirms the service items are for the same instance
        """
        if not other:
            return False
        return self.unique_identifier == other.unique_identifier

    def __ne__(self, other):
        """
        Confirms the service items are not for the same instance
        """
        return self.unique_identifier != other.unique_identifier

    def __hash__(self):
        """
        Return the hash for the service item.
        """
        return self.unique_identifier

    def is_media(self):
        """
        Confirms if the ServiceItem is media
        """
        return ItemCapabilities.RequiresMedia in self.capabilities

    def is_command(self):
        """
        Confirms if the ServiceItem is a command
        """
        return self.service_item_type == ServiceItemType.Command

    def is_image(self):
        """
        Confirms if the ServiceItem is an image
        """
        return self.service_item_type == ServiceItemType.Image

    def uses_file(self):
        """
        Confirms if the ServiceItem uses a file
        """
        return self.service_item_type == ServiceItemType.Image or self.service_item_type == ServiceItemType.Command

    def is_text(self):
        """
        Confirms if the ServiceItem is text
        """
        return self.service_item_type == ServiceItemType.Text

    def set_media_length(self, length):
        """
        Stores the media length of the item

        ``length``
            The length of the media item
        """
        self.media_length = length
        if length > 0:
            self.add_capability(ItemCapabilities.HasVariableStartTime)

    def get_frames(self):
        """
        Returns the frames for the ServiceItem
        """
        if self.service_item_type == ServiceItemType.Text:
            return self._display_frames
        else:
            return self._raw_frames

    def get_rendered_frame(self, row):
        """
        Returns the correct frame for a given list and renders it if required.
        ``row``
            The service item slide to be returned
        """
        if self.service_item_type == ServiceItemType.Text:
            return self._display_frames[row]['html'].split('\n')[0]
        elif self.service_item_type == ServiceItemType.Image:
            return self._raw_frames[row]['path']
        else:
            return self._raw_frames[row]['image']

    def get_frame_title(self, row=0):
        """
        Returns the title of the raw frame
        """
        try:
            return self._raw_frames[row]['title']
        except IndexError:
            return ''

    def get_frame_path(self, row=0, frame=None):
        """
        Returns the path of the raw frame
        """
        if not frame:
            try:
                frame = self._raw_frames[row]
            except IndexError:
                return ''
        if self.is_image():
            path_from = frame['path']
        else:
            path_from = os.path.join(frame['path'], frame['title'])
        return path_from

    def remove_frame(self, frame):
        """
        Remove the specified frame from the item
        """
        if frame in self._raw_frames:
            self._raw_frames.remove(frame)

    def get_media_time(self):
        """
        Returns the start and finish time for a media item
        """
        start = None
        end = None
        if self.start_time != 0:
            start = translate('OpenLP.ServiceItem', '<strong>Start</strong>: %s') % \
                str(datetime.timedelta(seconds=self.start_time))
        if self.media_length != 0:
            end = translate('OpenLP.ServiceItem', '<strong>Length</strong>: %s') % \
                str(datetime.timedelta(seconds=self.media_length))
        if not start and not end:
            return ''
        elif start and not end:
            return start
        elif not start and end:
            return end
        else:
            return '%s <br>%s' % (start, end)

    def update_theme(self, theme):
        """
        updates the theme in the service item

        ``theme``
            The new theme to be replaced in the service item
        """
        self.theme_overwritten = (theme is None)
        self.theme = theme
        self._new_item()
        self.render()

    def remove_invalid_frames(self, invalid_paths=None):
        """
        Remove invalid frames, such as ones where the file no longer exists.
        """
        if self.uses_file():
            for frame in self.get_frames():
                if self.get_frame_path(frame=frame) in invalid_paths:
                    self.remove_frame(frame)

    def missing_frames(self):
        """
        Returns if there are any frames in the service item
        """
        return not bool(self._raw_frames)

    def validate_item(self, suffix_list=None):
        """
        Validates a service item to make sure it is valid
        """
        self.is_valid = True
        for frame in self._raw_frames:
            if self.is_image() and not os.path.exists(frame['path']):
                self.is_valid = False
                break
            elif self.is_command():
                file_name = os.path.join(frame['path'], frame['title'])
                if not os.path.exists(file_name):
                    self.is_valid = False
                    break
                if suffix_list and not self.is_text():
                    file_suffix = frame['title'].split('.')[-1]
                    if file_suffix.lower() not in suffix_list:
                        self.is_valid = False
                        break

    def _get_renderer(self):
        """
        Adds the Renderer to the class dynamically
        """
        if not hasattr(self, '_renderer'):
            self._renderer = Registry().get('renderer')
        return self._renderer

    renderer = property(_get_renderer)

    def _get_image_manager(self):
        """
        Adds the image manager to the class dynamically
        """
        if not hasattr(self, '_image_manager'):
            self._image_manager = Registry().get('image_manager')
        return self._image_manager

    image_manager = property(_get_image_manager)
