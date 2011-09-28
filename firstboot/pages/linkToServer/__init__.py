# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

# This file is part of Guadalinex
#
# This software is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this package; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

__author__ = "Antonio Hernández <ahernandez@emergya.com>"
__copyright__ = "Copyright (C) 2011, Junta de Andalucía <devmaster@guadalinex.org>"
__license__ = "GPL-2"


import os
import gtk

import ServerConf
from ServerConf import ServerConfException, LinkToLDAPException, LinkToChefException
from firstboot_lib import PageWindow, FirstbootEntry

import gettext
from gettext import gettext as _
gettext.textdomain('firstboot')


__REQUIRED__ = False

__TITLE__ = _('Link workstation to a server')

__STATUS_TEST_PASSED__ = 0
__STATUS_CONFIG_CHANGED__ = 1
__STATUS_CONNECTING__ = 2
__STATUS_ERROR__ = 3


def get_page(options=None):

    page = LinkToServerPage(options)
    return page

class LinkToServerPage(PageWindow.PageWindow):
    __gtype_name__ = "LinkToServerPage"

    # To construct a new instance of this method, the following notable
    # methods are called in this order:
    # __new__(cls)
    # __init__(self)
    # finish_initializing(self, builder)
    # __init__(self)
    #
    # For this reason, it's recommended you leave __init__ empty and put
    # your initialization code in finish_initializing

    def finish_initializing(self, builder, options=None):
        """Called while initializing this instance in __new__

        finish_initializing should be called after parsing the UI definition
        and creating a FirstbootWindow object with it in order to finish
        initializing the start of the new FirstbootWindow instance.
        """

        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self, True)

        self.lblDescription = builder.get_object('lblDescription')
        self.chkUnlinkLDAP = builder.get_object('chkUnlinkLDAP')
        self.chkUnlinkChef = builder.get_object('chkUnlinkChef')
        self.radioManual = builder.get_object('radioManual')
        self.radioAuto = builder.get_object('radioAuto')
        self.lblUrl = builder.get_object('lblUrl')
        self.txtUrl = builder.get_object('txtUrl')
        self.imgStatus = builder.get_object('imgStatus')
        self.lblStatus = builder.get_object('lblStatus')
        self.btnLinkToServer = builder.get_object('btnLinkToServer')

        self.show_status()

        container = builder.get_object(self.__page_container__)
        page = builder.get_object(self.__gtype_name__)
        container.remove(page)
        self.page = page

        self.ldap_is_configured = ServerConf.ldap_is_configured()
        self.translate()

        if not self.ldap_is_configured:
            self.chkUnlinkLDAP.set_visible(False)
            self.chkUnlinkChef.set_visible(False)
            self.radioManual.set_visible(True)
            self.radioAuto.set_visible(True)
            self.lblUrl.set_visible(True)
            self.txtUrl.set_visible(True)
            self.btnLinkToServer.set_sensitive(True)

        else:
            self.chkUnlinkLDAP.set_visible(True)
            self.chkUnlinkChef.set_visible(True)
            self.radioManual.set_visible(False)
            self.radioAuto.set_visible(False)
            self.lblUrl.set_visible(False)
            self.txtUrl.set_visible(False)
            self.btnLinkToServer.set_sensitive(False)


        self.cmd_options = options
        self.fbe = FirstbootEntry.FirstbootEntry()

        url_config = self.fbe.get_url()
        url = self.cmd_options.url

        if url == None or len(url) == 0:
            url = url_config

        if url == None or len(url) == 0:
            url = ''

        self.txtUrl.set_text(url)

    def translate(self):
        desc = _('When a workstation is linked to a GECOS server it can be \
managed remotely and existing users in the server can login into \
this workstation.\n\n')

        if not self.ldap_is_configured:
            self.btnLinkToServer.set_label(_('Configure'))
            desc_detail = _('You can type the options manually or download \
a default configuration from the server.')
        else:
            self.btnLinkToServer.set_label(_('Unlink'))
            desc_detail = _('This workstation is currently linked to a GECOS \
server.')

        self.lblDescription.set_text(desc + desc_detail)
        self.chkUnlinkLDAP.set_label(_('Unlink from LDAP'))
        self.chkUnlinkChef.set_label(_('Unlink from Chef'))
        self.radioManual.set_label(_('Manual'))
        self.radioAuto.set_label(_('Automatic'))

    def get_widget(self):
        return self.page

    def on_chkUnlinkLDAP_toggle(self, button):
        active = button.get_active() | self.chkUnlinkChef.get_active()
        self.btnLinkToServer.set_sensitive(active)

    def on_chkUnlinkChef_toggle(self, button):
        active = button.get_active() | self.chkUnlinkLDAP.get_active()
        self.btnLinkToServer.set_sensitive(active)

    def on_radioManual_toggled(self, button):
        self.lblUrl.set_visible(False)
        self.txtUrl.set_visible(False)

    def on_radioAutomatic_toggled(self, button):
        self.lblUrl.set_visible(True)
        self.txtUrl.set_visible(True)

    def on_btnLinkToServer_Clicked(self, button):

        self.show_status()

        if self.ldap_is_configured:
            self.unlink_from_server()

        elif self.radioManual.get_active():
            self.emit('subpage-changed', 'linkToServer',
                      'LinkToServerConfEditorPage', {'server_conf': None})

        elif self.radioAuto.get_active():

            try:
                url = self.txtUrl.get_text()
                server_conf = ServerConf.get_server_conf(url)
                #self.show_status(__STATUS_TEST_PASSED__)
                self.emit('subpage-changed', 'linkToServer',
                          'LinkToServerConfEditorPage', {'server_conf': server_conf})

            except ServerConfException as e:
                self.show_status(__STATUS_ERROR__, e)

            except Exception as e:
                print e

    def unlink_from_server(self):

        errors = []
        messages = []

        if self.chkUnlinkLDAP.get_active():
            try:
                ret = ServerConf.unlink_from_ldap()
                if ret == True:
                    messages.append(_('Workstation has been unlinked from LDAP.'))
                else:
                    errors += ret
            except Exception as e:
                errors.append(str(e))

        if self.chkUnlinkChef.get_active():
            try:
                ret = ServerConf.unlink_from_chef()
                if ret == True:
                    messages.append(_('Workstation has been unlinked from Chef.'))
                else:
                    errors += ret
            except Exception as e:
                errors.append(str(e))

        result = not bool(len(errors))
        self.emit('subpage-changed', 'linkToServer',
            'LinkToServerResultsPage',
            {'result': result, 'server_conf': None,
            'errors': errors, 'messages': messages}
        )

    def show_status(self, status=None, exception=None):

        icon_size = gtk.ICON_SIZE_BUTTON

        if status == None:
            self.imgStatus.set_visible(False)
            self.lblStatus.set_visible(False)

        elif status == __STATUS_TEST_PASSED__:
            self.imgStatus.set_from_stock(gtk.STOCK_APPLY, icon_size)
            self.imgStatus.set_visible(True)
            self.lblStatus.set_label(_('The configuration file is valid.'))
            self.lblStatus.set_visible(True)

        elif status == __STATUS_CONFIG_CHANGED__:
            self.imgStatus.set_from_stock(gtk.STOCK_APPLY, icon_size)
            self.imgStatus.set_visible(True)
            self.lblStatus.set_label(_('The configuration was updated successfully.'))
            self.lblStatus.set_visible(True)

        elif status == __STATUS_ERROR__:
            self.imgStatus.set_from_stock(gtk.STOCK_DIALOG_ERROR, icon_size)
            self.imgStatus.set_visible(True)
            self.lblStatus.set_label(str(exception.args[0]))
            self.lblStatus.set_visible(True)

        elif status == __STATUS_CONNECTING__:
            self.imgStatus.set_from_stock(gtk.STOCK_CONNECT, icon_size)
            self.imgStatus.set_visible(True)
            self.lblStatus.set_label(_('Trying to connect...'))
            self.lblStatus.set_visible(True)
