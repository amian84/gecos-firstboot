
import os
import gtk
import gio
import pango
from firstboot_lib.Builder import Builder

import gettext
from gettext import gettext as _
gettext.textdomain('firstboot')

__REQUIRED__ = False

__TITLE__ = _('Run applications')

def get_page():

    page = RunApplicationsPage()
    return page

class RunApplicationsPage(gtk.Window):
    __gtype_name__ = "RunApplicationsPage"

    # To construct a new instance of this method, the following notable 
    # methods are called in this order:
    # __new__(cls)
    # __init__(self)
    # finish_initializing(self, builder)
    # __init__(self)
    #
    # For this reason, it's recommended you leave __init__ empty and put
    # your initialization code in finish_initializing

    def __new__(cls):
        """Special static method that's automatically called by Python when 
        constructing a new instance of this class.
        
        Returns a fully instantiated BaseFirstbootWindow object.
        """

        ui_filename = os.path.join(os.path.dirname(__file__), 'RunApplicationsPage.glade')

        builder = Builder()
        builder.set_translation_domain('firstboot')
        builder.add_from_file(ui_filename)

        new_object = builder.get_object("ContainerWindow")
        new_object.finish_initializing(builder)

        return new_object

    def finish_initializing(self, builder):
        """Called while initializing this instance in __new__

        finish_initializing should be called after parsing the UI definition
        and creating a FirstbootWindow object with it in order to finish
        initializing the start of the new FirstbootWindow instance.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self, True)

        container = builder.get_object('ContainerWindow')
        page = builder.get_object('RunApplicationsPage')
        container.remove(page)
        self.page = page

        self.ivApplications = builder.get_object('ivApplications')

        self.load_iconview()

    def get_widget(self):
        return self.page

    def load_iconview(self):

        self.ivApplications.set_selection_mode(gtk.SELECTION_SINGLE)

        store = self.ivApplications.get_model()
        store.clear()

        filter = ['firefox', 'gnome-terminal']
        app_list = gio.app_info_get_all()

        for app in app_list:
            if app.get_executable() in filter:

                icon = app.get_icon()
                pixbuf = None

                try:
                    if isinstance(icon, gio.FileIcon):
                        pixbuf = gtk.gdk.Pixbuf.from_file(icon).get_file().get_path()

                    elif isinstance(icon, gio.ThemedIcon):
                        theme = gtk.icon_theme_get_default()
                        pixbuf = theme.load_icon(icon.get_names()[0], 96, gtk.ICON_LOOKUP_USE_BUILTIN)

                except Exception, e:
                    print "Error loading icon pixbuf: " + e.message;

                store.append([
                    pixbuf, app.get_name(),
                    pango.ALIGN_CENTER, 140, pango.WRAP_WORD,
                    app
                ])

        self.ivApplications.set_model(store)

    def on_ivApplications_buttonReleased(self, iconview, event):
        try:
            path = iconview.get_path_at_pos(int(event.x), int(event.y))
            if path == None:
                raise Exception('No item selected')
            model = iconview.get_model()
            item = model.get_value(model.get_iter(path), 5)

            item.launch()

        except Exception, e:
            print e

    def on_ivApplications_activated(self, iconview):
        try:
            cursor = iconview.get_cursor()
            path = cursor[0]
            model = iconview.get_model()
            item = model.get_value(model.get_iter(path), 5)

            item.launch()

        except Exception, e:
            print e
