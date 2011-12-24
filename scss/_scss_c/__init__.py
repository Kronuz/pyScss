# -*- coding: utf-8 -*-

import sys
from ctypes import *
from os.path import join, dirname

if sys.platform == 'win32':
    ext = 'dll'
else:
    ext = 'so'

_scss = cdll.LoadLibrary(join(dirname(__file__), '_scss_c.%s' % ext))


########################################
# the Block struct
########################################

class Block(Structure):
    _fields_ = [
        ('_error', c_int),
        ('_lineno', c_int),
        ('_selprop', POINTER(c_char)),
        ('_selprop_sz', c_int),
        ('_codestr', POINTER(c_char)),
        ('_codestr_sz', c_int),
    ]

    def lineno_get(self):
        return self._lineno

    def lineno_set(self, value):
        raise AttributeError('lineno attribute is read only')
    lineno = property(lineno_get, lineno_set)

    def selprop_get(self):
        try:
            if self._selprop_sz:
                return string_at(self._selprop, self._selprop_sz)
            return ''
        except:
            raise

    def selprop_set(self, value):
        raise AttributeError('selprop attribute is read only')
    selprop = property(selprop_get, selprop_set)

    def codestr_get(self):
        try:
            if self._codestr_sz:
                return string_at(self._codestr, self._codestr_sz)
            return ''
        except:
            raise

    def codestr_set(self, value):
        raise AttributeError('codestr attribute is read only')
    codestr = property(codestr_get, codestr_set)

    def __nonzero__(self):
        return self._error != 0

    def __repr__(self):
        return '<Block %d %s>' % (self.lineno, self.selprop.__repr__())

    def __unicode__(self):
        return self.selprop


########################################
# Init function prototypes
########################################

_scss.block_locator_create.argtypes = [c_char_p, c_int]
_scss.block_locator_create.restype = c_void_p

_scss.block_locator_rewind.argtypes = [c_void_p]
_scss.block_locator_rewind.restype = None

_scss.block_locator_destroy.argtypes = [c_void_p]
_scss.block_locator_destroy.restype = None

_scss.block_locator_next_block.argtypes = [c_void_p]
_scss.block_locator_next_block.restype = POINTER(Block)


########################################
# Python API
########################################

class BlockLocator(object):
    def __init__(self, codestr):
        """
        Create a BlockLocator instance to segment codestr.
        """
        self._unicode = False
        self._destroyed = False
        if isinstance(codestr, unicode):
            codestr = codestr.encode('utf8')
            self._unicode = True
        self._locator = _scss.block_locator_create(codestr, len(codestr))

    def __iter__(self):
        """
        Iterate through all blocks. Note the iteration has
        side-effect: an BlockLocator object can only be iterated
        once.
        """
        while True:
            block = self.next_block()
            if block is None:
                raise StopIteration
            if self._unicode:
                yield block.lineno, block.selprop.decode('utf8'), block.codestr.decode('utf8')
            else:
                yield block.lineno, block.selprop, block.codestr

    def next_block(self):
        """
        Get next block. When no block is available, return None.
        """
        if self._destroyed:
            return None

        block = _scss.block_locator_next_block(self._locator)
        block = block.contents
        if block._error >= 0:
            _scss.block_locator_rewind(self._locator)
            if block._error > 0:
                raise Exception({
                    1: "Missing closing parenthesis somewhere in block",
                    2: "Missing closing string somewhere in block",
                    3: "Block never closed",
                }.get(block._error), block._error)
            return None
        else:
            return block

    def __del__(self):
        if not self._destroyed:
            _scss.block_locator_destroy(self._locator)
            self._destroyed = True

locate_blocks = BlockLocator
