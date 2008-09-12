#------------------------------------------------------------------------------
# Copyright (c) 2007, Riverbank Computing Limited
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license.
#
# Author: Riverbank Computing Limited
#------------------------------------------------------------------------------

""" Defines file editors and the file editor factory for the PyQt user 
    interface toolkit.
"""

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

from os.path \
    import splitext, isfile, exists

from PyQt4 import QtCore, QtGui

from enthought.traits.api \
    import List, Str, Event, Bool, Int, Unicode, TraitError

from enthought.traits.ui.api \
    import View, Group

from text_editor \
    import ToolkitEditorFactory as EditorFactory, \
           SimpleEditor         as SimpleTextEditor

#-------------------------------------------------------------------------------
#  Trait definitions:
#-------------------------------------------------------------------------------

# Wildcard filter:
filter_trait = List(Unicode)

#-------------------------------------------------------------------------------
#  'ToolkitEditorFactory' class:
#-------------------------------------------------------------------------------

class ToolkitEditorFactory ( EditorFactory ):
    """ PyQt editor factory for file editors.
    """

    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------

    # Wildcard filter to apply to the file dialog:
    filter = filter_trait

    # Optional extended trait name of the trait containing the list of filters:
    filter_name = Str

    # Should file extension be truncated?
    truncate_ext = Bool( False )

    # Can the user select directories as well as files?
    allow_dir = Bool( False )

    # Is user input set on every keystroke? (Overrides the default) ('simple' 
    # style only):
    auto_set = False      

    # Is user input set when the Enter key is pressed? (Overrides the default)
    # ('simple' style only):
    enter_set = True

    # The number of history entries to maintain:
    # FIXME: add support
    entries = Int( 10 )

    # Optional extended trait name used to notify the editor when the file 
    # system view should be reloaded ('custom' style only):
    reload_name = Str

    # Optional extended trait name used to notify when the user double-clicks
    # an entry in the file tree view:
    dclick_name = Str

    #---------------------------------------------------------------------------
    #  Traits view definition:  
    #---------------------------------------------------------------------------

    traits_view = View( [ [ '<options>',
                        'truncate_ext{Automatically truncate file extension?}',
                        '|options:[Options]>' ],
                          [ 'filter', '|[Wildcard filters]<>' ] ] )

    extras = Group()

    #---------------------------------------------------------------------------
    #  'Editor' factory methods:
    #---------------------------------------------------------------------------

    def simple_editor ( self, ui, object, name, description, parent ):
        return SimpleEditor( parent,
                             factory     = self, 
                             ui          = ui, 
                             object      = object, 
                             name        = name, 
                             description = description ) 

    def custom_editor ( self, ui, object, name, description, parent ):
        return CustomEditor( parent,
                             factory     = self, 
                             ui          = ui, 
                             object      = object, 
                             name        = name, 
                             description = description ) 

#-------------------------------------------------------------------------------
#  'SimpleEditor' class:
#-------------------------------------------------------------------------------

class SimpleEditor ( SimpleTextEditor ):
    """ Simple style of file editor, consisting of a text field and a **Browse**
        button that opens a file-selection dialog box. The user can also drag 
        and drop a file onto this control.
    """

    #---------------------------------------------------------------------------
    #  Finishes initializing the editor by creating the underlying toolkit
    #  widget:
    #---------------------------------------------------------------------------

    def init ( self, parent ):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        # The control is a horizontal layout.
        self.control = QtGui.QHBoxLayout()

        self._file_name = control = QtGui.QLineEdit()

        if self.factory.auto_set:
            QtCore.QObject.connect(control,
                    QtCore.SIGNAL('textEdited(QString)'), self.update_object)
        else:
            # Assume enter_set is set, otherwise the value will never get
            # updated.
            QtCore.QObject.connect(control, QtCore.SIGNAL('editingFinished()'),
                    self.update_object)

        self.control.addWidget(control)

        button = QtGui.QPushButton("Browse...")
        QtCore.QObject.connect(button, QtCore.SIGNAL('clicked()'),
                self.show_file_dialog)
        self.control.addWidget(button)

        self.set_tooltip(control)

    #---------------------------------------------------------------------------
    #  Handles the user changing the contents of the edit control:
    #---------------------------------------------------------------------------

    def update_object(self):
        """ Handles the user changing the contents of the edit control.
        """
        self._update(unicode(self._file_name.text()))

    #---------------------------------------------------------------------------
    #  Updates the editor when the object trait changes external to the editor:
    #---------------------------------------------------------------------------

    def update_editor ( self ):
        """ Updates the editor when the object trait changes externally to the 
            editor.
        """
        self._file_name.setText(self.str_value)

    #---------------------------------------------------------------------------
    #  Displays the pop-up file dialog:
    #---------------------------------------------------------------------------

    def show_file_dialog(self):
        """ Displays the pop-up file dialog.
        """
        # We don't used the canned functions because we don't know how the
        # file name is to be used (ie. an existing one to be opened or a new
        # one to be created).
        dlg = self._create_file_dialog()

        if dlg.exec_() == QtGui.QDialog.Accepted:
            files = dlg.selectedFiles()

            if len(files) > 0:
                file_name = unicode(files[0])

                if self.factory.truncate_ext:
                    file_name = splitext(file_name)[0]

                self.value = file_name
                self.update_editor()

    #---------------------------------------------------------------------------
    #  Returns the editor's control for indicating error status:
    #---------------------------------------------------------------------------

    def get_error_control ( self ):
        """ Returns the editor's control for indicating error status.
        """
        return self._file_name

    #-- Private Methods --------------------------------------------------------

    def _create_file_dialog ( self ):
        """ Creates the correct type of file dialog.
        """
        dlg = QtGui.QFileDialog(self.control.parentWidget())
        dlg.selectFile(self._file_name.text())

        if len(self.factory.filter) > 0:
            dlg.setFilters(self.factory.filter)

        return dlg

    def _update ( self, file_name ):
        """ Updates the editor value with a specified file name.
        """
        try:
            if self.factory.truncate_ext:
                file_name = splitext( file_name )[0]

            self.value = file_name
        except TraitError, excp:
            pass

#-------------------------------------------------------------------------------
#  'CustomEditor' class:
#-------------------------------------------------------------------------------

class CustomEditor ( SimpleTextEditor ):
    """ Custom style of file editor, consisting of a file system tree view.
    """

    # Is the file editor scrollable? This value overrides the default.
    scrollable = True

    # Wildcard filter to apply to the file dialog:
    filter = filter_trait

    # Event fired when the file system view should be rebuilt:
    reload = Event

    # Event fired when the user double-clicks a file:
    dclick = Event

    #---------------------------------------------------------------------------
    #  Finishes initializing the editor by creating the underlying toolkit
    #  widget:
    #---------------------------------------------------------------------------

    def init ( self, parent ):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        self.control = _TreeView(self)

        self._model = model = QtGui.QDirModel()
        self.control.setModel(model)

        factory = self.factory
        self.filter = factory.filter
        self.sync_value(factory.filter_name, 'filter', 'from', is_list=True)
        self.sync_value(factory.reload_name, 'reload', 'from')
        self.sync_value(factory.dclick_name, 'dclick', 'to')

        self.set_tooltip()

    #---------------------------------------------------------------------------
    #  Handles the user changing the contents of the edit control:
    #---------------------------------------------------------------------------

    def update_object(self, idx):
        """ Handles the user changing the contents of the edit control.
        """
        if self.control is not None:
            path = unicode(self._model.filePath(idx))

            if self.factory.allow_dir or isfile(path):
                if self.factory.truncate_ext:
                    path = splitext( path )[0]

                self.value = path

    #---------------------------------------------------------------------------
    #  Updates the editor when the object trait changes external to the editor:
    #---------------------------------------------------------------------------

    def update_editor ( self ):
        """ Updates the editor when the object trait changes externally to the 
            editor.
        """
        if exists(self.str_value):
            self.control.setCurrentIndex(self._model.index(self.str_value))

    #---------------------------------------------------------------------------
    #  Handles the 'filter' trait being changed:
    #---------------------------------------------------------------------------

    def _filter_changed ( self ):
        """ Handles the 'filter' trait being changed.
        """
        self._model.setNameFilters(self.filter)

    #---------------------------------------------------------------------------
    #  Handles the user double-clicking on a file name:
    #---------------------------------------------------------------------------

    def _on_dclick ( self, idx ):
        """ Handles the user double-clicking on a file name.
        """
        self.dclick = True

    #---------------------------------------------------------------------------
    #  Handles the 'reload' trait being changed:
    #---------------------------------------------------------------------------

    def _reload_changed ( self ):
        """ Handles the 'reload' trait being changed.
        """
        self._model.refresh()

#-------------------------------------------------------------------------------
#  '_TreeView' class:
#-------------------------------------------------------------------------------

class _TreeView(QtGui.QTreeView):
    """ This is an internal class needed because QAbstractItemView (for some
        strange reason) doesn't provide a signal when the current index
        changes.
    """

    def __init__(self, editor):

        QtGui.QTreeView.__init__(self)

        self.connect(self, QtCore.SIGNAL('doubleClicked(QModelIndex)'),
                editor._on_dclick)

        self._editor = editor

    def currentChanged(self, curr, prev):
        """ Reimplemented to tell the editor when the current index has
            changed.
        """

        QtGui.QTreeView.currentChanged(self, curr, prev)

        self._editor.update_object(curr)
