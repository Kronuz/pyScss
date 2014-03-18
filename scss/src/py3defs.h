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
#ifndef PY3DEFS_H
#define PY3DEFS_H

/* Iterators are turned on by default in Python 3. */
#if PY_MAJOR_VERSION >= 3
	#define Py_TPFLAGS_HAVE_ITER 0
#endif

/* Py_TYPE exists in 2.6+, but for 2.5 and below we can use the old ob_type. */
#ifndef Py_TYPE
    #define Py_TYPE(ob) (((PyObject*)(ob))->ob_type)
#endif

/* PyVarObject_HEAD_INIT also exists in 2.6+, so for 2.5 use PyObject_HEAD_INIT. */
#ifndef PyVarObject_HEAD_INIT
    #define PyVarObject_HEAD_INIT(type, size) PyObject_HEAD_INIT(type) size,
#endif

#endif
