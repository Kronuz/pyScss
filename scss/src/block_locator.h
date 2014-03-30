/*
* pyScss, a Scss compiler for Python
* SCSS blocks scanner.
*
* German M. Bravo (Kronuz) <german.mb@gmail.com>
* https://github.com/Kronuz/pyScss
*
* MIT license (http://www.opensource.org/licenses/mit-license.php)
* Copyright (c) 2011 German M. Bravo (Kronuz), All rights reserved.
*/
#include <Python.h>

#ifndef BLOCK_LOCATOR_H
#define BLOCK_LOCATOR_H

#define MAX_EXC_STRING 4096

typedef struct {
    int error;
    int lineno;
    Py_UNICODE *selprop;
    int selprop_sz;
    Py_UNICODE *codestr;
    int codestr_sz;
} Block;

typedef struct _lineno_stack {
    int lineno;
    struct _lineno_stack* next;
} _lineno_stack;

typedef struct {
    char exc[MAX_EXC_STRING];
    PyUnicodeObject *py_codestr;
    Py_UNICODE *codestr;
    Py_UNICODE *codestr_ptr;
    Py_ssize_t codestr_sz;
    _lineno_stack* lineno_stack;
    int lineno;
    int par;
    Py_UNICODE instr;
    int depth;
    int skip;
    Py_UNICODE *init;
    Py_UNICODE *lose;
    Py_UNICODE *start;
    Py_UNICODE *end;
    Block block;
} BlockLocator;

void BlockLocator_initialize(void);
void BlockLocator_finalize(void);

Block* BlockLocator_iternext(BlockLocator *self);
BlockLocator *BlockLocator_new(PyUnicodeObject *codestr);
void BlockLocator_del(BlockLocator *self);

#endif
