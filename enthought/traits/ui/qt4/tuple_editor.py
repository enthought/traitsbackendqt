#------------------------------------------------------------------------------
# Copyright (c) 2007, Riverbank Computing Limited
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD v2
# license.
#
# Author: Riverbank Computing Limited
#------------------------------------------------------------------------------

""" Defines the tuple editor and the tuple editor factory, for the PyQt 
user interface toolkit.
"""

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

from enthought.traits.trait_base \
    import SequenceTypes, enumerate
    
from enthought.traits.api \
    import HasTraits, List, Tuple, Unicode, Int, Any
    
from enthought.traits.ui.api \
    import View, Group, Item, EditorFactory as UIEditorFactory
    
from editor \
    import Editor
    
from editor_factory \
    import EditorFactory

#-------------------------------------------------------------------------------
#  'ToolkitEditorFactory' class:
#-------------------------------------------------------------------------------

class ToolkitEditorFactory ( EditorFactory ):
    """ PyQt editor factory for tuple editors.
    """
    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------
    
    # Trait definitions for each tuple field
    traits = Any         

    # Labels for each of the tuple fields
    labels = List( Unicode ) 

    # Editors for each of the tuple fields:
    editors = List( UIEditorFactory )

    # Number of tuple fields or rows
    cols   = Int( 1 )    
    
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
                                      
#-------------------------------------------------------------------------------
#  'SimpleEditor' class:
#-------------------------------------------------------------------------------
                               
class SimpleEditor ( Editor ):
    """ Simple style of editor for tuples.
    
    The editor displays an editor for each of the fields in the tuple, based on
    the type of each field. 
    """
    #---------------------------------------------------------------------------
    #  Finishes initializing the editor by creating the underlying toolkit
    #  widget:
    #---------------------------------------------------------------------------
        
    def init ( self, parent ):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        self._ts     = ts = TupleStructure( self )
        self._ui     = ui = ts.view.ui( ts, parent, kind = 'subpanel' ).set(
                                        parent = self.ui )
        self.control = ui.control
        self.set_tooltip()
        
    #---------------------------------------------------------------------------
    #  Updates the editor when the object trait changes external to the editor:
    #---------------------------------------------------------------------------
        
    def update_editor ( self ):
        """ Updates the editor when the object trait changes external to the 
            editor.
        """
        ts = self._ts
        for i, value in enumerate( self.value ):
            setattr( ts, 'f%d' % i, value ) 

    #---------------------------------------------------------------------------
    #  Returns the editor's control for indicating error status:
    #---------------------------------------------------------------------------

    def get_error_control ( self ):
        """ Returns the editor's control for indicating error status.
        """
        return self._ui.get_error_controls()

#-------------------------------------------------------------------------------
#  'TupleStructure' class:
#-------------------------------------------------------------------------------
        
class TupleStructure ( HasTraits ):
    """ Creates a view containing items for each field in a tuple.
    """
    #---------------------------------------------------------------------------
    #  Trait definitions:  
    #---------------------------------------------------------------------------
    
    # Editor this structure is linked to
    editor = Any
    
    # The constructed View for the tuple
    view = Any
    
    # Number of tuple fields
    fields = Int
    
    #---------------------------------------------------------------------------
    #  Initializes the object:
    #---------------------------------------------------------------------------
    
    def __init__ ( self, editor ):
        """ Initializes the object.
        """
        factory = editor.factory
        traits  = factory.traits
        labels  = factory.labels
        editors = factory.editors
        cols    = factory.cols
        
        # Save the reference to the editor:
        self.editor = editor
        
        # Get the tuple we are mirroring:
        object = editor.value
        
        # For each tuple field, add a trait with the appropriate trait 
        # definition and default value:
        content     = []
        self.fields = len( object )
        len_labels  = len( labels )
        len_editors = len( editors )

        if traits is None:
            type = editor.value_trait.handler
            if isinstance( type, Tuple ):
                traits = type.traits

        if not isinstance( traits, SequenceTypes ):
            traits = [ traits ]

        len_traits = len( traits )
        if len_traits == 0:
            traits     = [ Any ]
            len_traits = 1
            
        for i, value in enumerate( object ):
            trait = traits[ i % len_traits ]

            label = ''
            if i < len_labels:
                label = labels[i]

            editor = None
            if i < len_editors:
                editor = editors[i]

            name = 'f%d' % i
            self.add_trait( name, trait( value, event = 'field' ) )
            item = Item( name = name, label = label, editor = editor )
            if cols <= 1:
                content.append( item )
            else:
                if (i % cols) == 0:
                    group = Group( orientation = 'horizontal' )
                    content.append( group )

                group.content.append( item )

        self.view = View( Group( show_labels = (len_labels != 0), *content ) )

    #---------------------------------------------------------------------------
    #  Updates the underlying tuple when any field changes value:
    #---------------------------------------------------------------------------
                
    def _field_changed ( self ):
        """ Updates the underlying tuple when any field changes value.
        """
        self.editor.value = tuple( [ getattr( self, 'f%d' % i ) 
                                     for i in range( self.fields ) ] )
