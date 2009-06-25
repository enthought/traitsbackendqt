#------------------------------------------------------------------------------
# Copyright (c) 2009, Enthought, Inc.
# All rights reserved.
# 
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
# 
# Author: Evan Patterson
# Date: 06/25/09
#------------------------------------------------------------------------------

""" A renderer which will display a cell-specific image in addition to some
    text displayed in the same way the default renderer would.
"""

# System library imports
from PyQt4 import QtCore, QtGui


class TableImageRenderer(QtGui.QStyledItemDelegate):
    """ A renderer which will display a cell-specific image in addition to some
        text displayed in the same way the default renderer would.
    """

    #---------------------------------------------------------------------------
    #  TableImageRenderer interface
    #---------------------------------------------------------------------------
    
    def get_image_for_obj(self, value, row, col):
        """ Return the image for the cell given the raw cell value and the row
            and column numbers.
        """
        return None

    #---------------------------------------------------------------------------
    #  QAbstractItemDelegate interface
    #---------------------------------------------------------------------------

    def paint(self, painter, option, index):
        """ Overriden to draw images.
        """
        # First draw any text/backgroudn by delegating to our superclass
        QtGui.QStyledItemDelegate.paint(self, painter, option, index)

        # Now draw the image, if possible
        value = index.data(QtCore.Qt.UserRole).toPyObject()
        image = self.get_image_for_obj(value, index.row(), index.column())
        if image:
            image = image.create_bitmap()
            w = min(image.width(), option.rect.width())
            h = min(image.height(), option.rect.height())
            target = QtCore.QRect(option.rect.x(), option.rect.y(), w, h)
            painter.drawPixmap(target, image)

    def sizeHint(self, option, index):
        """ Overriden to take image size into account when providing a size 
            hint.
        """
        size = QtGui.QStyledItemDelegate.sizeHint(self, option, index)

        value = index.data(QtCore.Qt.UserRole).toPyObject()
        image = self.get_image_for_obj(value, index.row(), index.column())
        if image:
            image = image.create_bitmap()
            size.setWidth(max(image.width(), size.width()))
            size.setHeight(max(image.height(), size.height()))

        return size
