#------------------------------------------------------------------------------
# Copyright (c) 2007, Riverbank Computing Limited
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD license.
# However, when used with the GPL version of PyQt the additional terms described in the PyQt GPL exception also apply

#
# Author: Riverbank Computing Limited
# Description: <Enthought pyface package component>
#------------------------------------------------------------------------------


# Major package imports.
from enthought.qt import QtCore, QtGui

# Enthought library imports.
from enthought.traits.api import Any, Event, implements, Property, Unicode
from enthought.traits.api import Tuple

# Local imports.
from enthought.pyface.i_window import IWindow, MWindow
from enthought.pyface.key_pressed_event import KeyPressedEvent
from gui import GUI
from widget import Widget


class Window(MWindow, Widget):
    """ The toolkit specific implementation of a Window.  See the IWindow
    interface for the API documentation.
    """

    implements(IWindow)

    #### 'IWindow' interface ##################################################

    position = Property(Tuple)

    size = Property(Tuple)

    title = Unicode

    #### Events #####

    activated = Event

    closed =  Event

    closing =  Event

    deactivated = Event

    key_pressed = Event(KeyPressedEvent)

    opened = Event

    opening = Event

    #### Private interface ####################################################

    # Shadow trait for position.
    _position = Tuple((-1, -1))

    # Shadow trait for size.
    _size = Tuple((-1, -1))

    ###########################################################################
    # 'IWindow' interface.
    ###########################################################################

    def activate(self):
        self.control.activateWindow()
        self.control.raise_()

    def show(self, visible):
        self.control.setVisible(visible)

    ###########################################################################
    # Protected 'IWindow' interface.
    ###########################################################################

    def _add_event_listeners(self):
        self._event_filter = _EventFilter(self)

    ###########################################################################
    # 'IWidget' interface.
    ###########################################################################

    def destroy(self):
        self._event_filter = None

        if self.control is not None:
            # Avoid problems with recursive calls.
            control = self.control
            self.control = None

            # Hide the widget before closing it. This is not strictly necessary
            # (closing the window in fact hides it), but the close may
            # trigger an application shutdown, which can take a long time.
            # The window should not be visible during this process.
            control.hide()
            control.close()

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _get_position(self):
        """ Property getter for position. """

        return self._position

    def _set_position(self, position):
        """ Property setter for position. """

        if self.control is not None:
            self.control.move(*position)

        old = self._position
        self._position = position

        self.trait_property_changed('position', old, position)

    def _get_size(self):
        """ Property getter for size. """

        return self._size

    def _set_size(self, size):
        """ Property setter for size. """

        if self.control is not None:
            self.control.resize(*size)

        old = self._size
        self._size = size

        self.trait_property_changed('size', old, size)

    def _title_changed(self, title):
        """ Static trait change handler. """

        if self.control is not None:
            self.control.setWindowTitle(title)


class _EventFilter(QtCore.QObject):
    """ An internal class that watches for certain events on behalf of the
    Window instance.
    """

    def __init__(self, window):
        """ Initialise the event filter. """

        QtCore.QObject.__init__(self)

        window.control.installEventFilter(self)
        self._window = window

    def eventFilter(self, obj, e):
        """ Adds any event listeners required by the window. """

        window = self._window

        # Sanity check.
        if obj is not window.control:
            return False

        if e.type() == QtCore.QEvent.Close:
            # Do not destroy the window during its event handler.
            GUI.invoke_later(window.close)

            if window.control is not None:
                e.ignore()

            return True

        if e.type() == QtCore.QEvent.WindowActivate:
            window.activated = window

        elif e.type() == QtCore.QEvent.WindowDeactivate:
            window.deactivated = window

        elif e.type() == QtCore.QEvent.Resize:
            # Get the new size and set the shadow trait without performing
            # notification.
            size = e.size()
            window._size = (size.width(), size.height())

        elif e.type() == QtCore.QEvent.Move:
            # Get the real position and set the trait without performing
            # notification.
            pos = e.pos()
            window._position = (pos.x(), pos.y())

        elif e.type() == QtCore.QEvent.KeyPress:
            # Pyface doesn't seem to be Unicode aware.  Only keep the key code
            # if it corresponds to a single Latin1 character.
            kstr = e.text()
            try:
                kcode = ord(str(kstr))
            except:
                kcode = 0

            mods = e.modifiers()
            window.key_pressed = KeyPressedEvent(
                alt_down     = ((mods & QtCore.Qt.AltModifier) ==
                                QtCore.Qt.AltModifier),
                control_down = ((mods & QtCore.Qt.ControlModifier) ==
                                QtCore.Qt.ControlModifier),
                shift_down   = ((mods & QtCore.Qt.ShiftModifier) ==
                                QtCore.Qt.ShiftModifier),
                key_code     = kcode,
                event        = e)

        return False

#### EOF ######################################################################
