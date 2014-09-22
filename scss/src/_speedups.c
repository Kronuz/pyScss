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
#include "py3defs.h"
#include "block_locator.h"
#include "scanner.h"

/* BlockLocator */
static PyTypeObject scss_BlockLocatorType;

typedef struct {
	PyObject_HEAD
	BlockLocator *locator;
} scss_BlockLocator;

static char*
scss_pyunicode_to_utf8(PyObject* obj, int* len)
{
	char* internal_buffer;
	char* ret;
	PyObject* intermediate_bytes;

	intermediate_bytes = PyUnicode_AsUTF8String(obj);
	assert(intermediate_bytes != NULL);
	internal_buffer = PyBytes_AsString(intermediate_bytes);
	*len = (int)PyBytes_Size(intermediate_bytes);
	ret = PyMem_New(char, *len + 1);
	memcpy(ret, internal_buffer, *len + 1);
	Py_DECREF(intermediate_bytes);
	return ret;
}

static int
scss_BlockLocator_init(scss_BlockLocator *self, PyObject *args, PyObject *kwds)
{
	PyUnicodeObject *codestr;
	int codestr_sz;

	self->locator = NULL;

	if (!PyArg_ParseTuple(args, "U", &codestr, &codestr_sz)) {
		return -1;
	}

	self->locator = BlockLocator_new(codestr);

	#ifdef DEBUG
		PySys_WriteStderr("Scss BlockLocator object initialized! (%lu bytes)\n", sizeof(scss_BlockLocator));
	#endif

	return 0;
}

static void
scss_BlockLocator_dealloc(scss_BlockLocator *self)
{
	if (self->locator != NULL) BlockLocator_del(self->locator);

	Py_TYPE(self)->tp_free((PyObject*)self);

	#ifdef DEBUG
		PySys_WriteStderr("Scss BlockLocator object destroyed!\n");
	#endif
}

scss_BlockLocator*
scss_BlockLocator_iter(scss_BlockLocator *self)
{
	Py_INCREF(self);
	return self;
}

PyObject*
scss_BlockLocator_iternext(scss_BlockLocator *self)
{
	Block *block;

	if (self->locator != NULL) {
		block = BlockLocator_iternext(self->locator);

		if (block->error > 0) {
			return Py_BuildValue(
				"iu#u#",
				block->lineno,
				block->selprop,
				block->selprop_sz,
				block->codestr,
				block->codestr_sz
			);
		}

		if (block->error < 0) {
			PyErr_SetString(PyExc_Exception, self->locator->exc);
			return NULL;
		}
	}

	/* Raising of standard StopIteration exception with empty value. */
	PyErr_SetNone(PyExc_StopIteration);
	return NULL;
}

/* Type definition */

static PyTypeObject scss_BlockLocatorType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"scss._BlockLocator",                      /* tp_name */
	sizeof(scss_BlockLocator),                 /* tp_basicsize */
	0,                                         /* tp_itemsize */
	(destructor)scss_BlockLocator_dealloc,     /* tp_dealloc */
	0,                                         /* tp_print */
	0,                                         /* tp_getattr */
	0,                                         /* tp_setattr */
	0,                                         /* tp_compare */
	0,                                         /* tp_repr */
	0,                                         /* tp_as_number */
	0,                                         /* tp_as_sequence */
	0,                                         /* tp_as_mapping */
	0,                                         /* tp_hash  */
	0,                                         /* tp_call */
	0,                                         /* tp_str */
	0,                                         /* tp_getattro */
	0,                                         /* tp_setattro */
	0,                                         /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_ITER, /* tp_flags */
	"Internal BlockLocator iterator object.",  /* tp_doc */
	0,                                         /* tp_traverse */
	0,                                         /* tp_clear */
	0,                                         /* tp_richcompare */
	0,                                         /* tp_weaklistoffset */
	(getiterfunc)scss_BlockLocator_iter,       /* tp_iter: __iter__() method */
	(iternextfunc)scss_BlockLocator_iternext,  /* tp_iternext: next() method */
	0,                                         /* tp_methods */
	0,                                         /* tp_members */
	0,                                         /* tp_getset */
	0,                                         /* tp_base */
	0,                                         /* tp_dict */
	0,                                         /* tp_descr_get */
	0,                                         /* tp_descr_set */
	0,                                         /* tp_dictoffset */
	(initproc)scss_BlockLocator_init,          /* tp_init */
};


/* Scanner */
static PyObject *PyExc_scss_NoMoreTokens;

static PyTypeObject scss_ScannerType;

typedef struct {
	PyObject_HEAD
	Scanner *scanner;
	PyObject *py_input;
} scss_Scanner;


static PyObject *
scss_Scanner_rewind(scss_Scanner *self, PyObject *args)
{
	int token_num;
	if (self->scanner != NULL) {
		if (PyArg_ParseTuple(args, "i", &token_num)) {
			Scanner_rewind(self->scanner, token_num);
		}
	}
	Py_INCREF(Py_None);
	return (PyObject *)Py_None;
}


static PyObject *
scss_Scanner_token(scss_Scanner *self, PyObject *args)
{
	PyObject *iter;
	PyObject *item;
	long size, hash;

	Token *p_token;
	PyObject *py_tok;
	PyObject *py_token;

	char *tok;
	int token_num, len;
	PyObject *restrictions = NULL;
	Hashtable *_restrictions = NULL;

	if (self->scanner != NULL) {
		if (PyArg_ParseTuple(args, "i|O", &token_num, &restrictions)) {
			if (restrictions != NULL) {
				hash = PyObject_Hash(restrictions);
				_restrictions = Hashtable_get(self->scanner->restrictions_cache, &hash, sizeof(hash));
				if (_restrictions == NULL) {
					size = PySequence_Size(restrictions);
					if (size != -1) {
						_restrictions = Hashtable_create(64);
						iter = PyObject_GetIter(restrictions);
						while ((item = PyIter_Next(iter))) {
							if (PyUnicode_Check(item)) {
								tok = scss_pyunicode_to_utf8(item, &len);
								Hashtable_set(_restrictions, tok, len + 1, (void *)-1);
							}
							Py_DECREF(item);
						}
						Py_DECREF(iter);
					}
					Hashtable_set(self->scanner->restrictions_cache, &hash, sizeof(hash), _restrictions);
				}
			}

			p_token = Scanner_token(self->scanner, token_num, _restrictions);

			if (p_token == (Token *)SCANNER_EXC_BAD_TOKEN
				|| p_token == (Token *)SCANNER_EXC_RESTRICTED)
			{
				PyObject *scss_errors_module = PyImport_ImportModule("scss.errors");
				PyObject *syntax_error_cls = PyObject_GetAttrString(scss_errors_module, "SassSyntaxError");
				PyObject *position = PyLong_FromLong(self->scanner->pos);
				PyObject *syntax_error = PyObject_CallFunctionObjArgs(
					syntax_error_cls, self->py_input, position, restrictions, NULL);
				Py_DECREF(scss_errors_module);
				Py_DECREF(position);
				PyErr_SetObject(syntax_error_cls, syntax_error);
				Py_DECREF(syntax_error_cls);
				Py_DECREF(syntax_error);
				return NULL;
			}
			if (p_token == (Token *)SCANNER_EXC_UNIMPLEMENTED) {
				PyErr_SetString(PyExc_NotImplementedError, self->scanner->exc);
				return NULL;
			}
			if (p_token == (Token *)SCANNER_EXC_NO_MORE_TOKENS) {
				PyErr_SetNone(PyExc_scss_NoMoreTokens);
				return NULL;
			}
			if (p_token < 0) {
				PyErr_SetNone(PyExc_Exception);
				return NULL;
			}

			py_tok = PyUnicode_DecodeUTF8(p_token->regex->tok, strlen(p_token->regex->tok), "strict");
			if (py_tok == NULL) {
				return NULL;
			}

			py_token = PyUnicode_DecodeUTF8(p_token->string, p_token->string_sz, "strict");
			if (py_token == NULL) {
				return NULL;
			}

			return Py_BuildValue(
				"iiOO",
				p_token->string - self->scanner->input,
				p_token->string - self->scanner->input + p_token->string_sz,
				py_tok,
				py_token
			);
		}
	}
	Py_INCREF(Py_None);
	return (PyObject *)Py_None;
}

static PyObject *
scss_Scanner_reset(scss_Scanner *self, PyObject *args, PyObject *kwds)
{
	char *input = NULL;
	int input_sz = 0;

	if (self->scanner != NULL) {
		if (PyArg_ParseTuple(args, "|z#", &input, &input_sz)) {
			Scanner_reset(self->scanner, input, input_sz);
		}
	}

	Py_INCREF(Py_None);
	return (PyObject *)Py_None;
}

static PyObject *
scss_Scanner_setup_patterns(PyObject *self, PyObject *patterns)
{
	PyObject *item, *item0, *item1;
	int i, is_tuple, _is_tuple;
	long size;

	Pattern *_patterns = NULL;
	int patterns_sz = 0;
	int len;
	if (!Scanner_initialized()) {
		is_tuple = PyTuple_Check(patterns);
		if (is_tuple || PyList_Check(patterns)) {
			size = is_tuple ? PyTuple_Size(patterns) : PyList_Size(patterns);
			_patterns = PyMem_New(Pattern, size);
			for (i = 0; i < size; ++i) {
				item = is_tuple ? PyTuple_GetItem(patterns, i) : PyList_GetItem(patterns, i);
				_is_tuple = PyTuple_Check(item);
				if (_is_tuple || PyList_Check(item)) {
					item0 = _is_tuple ? PyTuple_GetItem(item, 0) : PyList_GetItem(item, 0);
					item1 = _is_tuple ? PyTuple_GetItem(item, 1) : PyList_GetItem(item, 1);
					if (PyUnicode_Check(item0) && PyUnicode_Check(item1)) {
						_patterns[patterns_sz].tok = scss_pyunicode_to_utf8(item0, &len);
						_patterns[patterns_sz].expr = scss_pyunicode_to_utf8(item1, &len);
						patterns_sz++;
					}
				}
			}
		}
		Scanner_initialize(_patterns, patterns_sz);
		if (_patterns != NULL) PyMem_Del(_patterns);
	}
	Py_INCREF(Py_None);
	return (PyObject *)Py_None;
}

static int
scss_Scanner_init(scss_Scanner *self, PyObject *args, PyObject *kwds)
{
	PyObject *item, *item0, *item1;
	int i, is_tuple, _is_tuple;
	long size;

	PyObject *patterns, *ignore;
	Pattern *_patterns = NULL;
	int patterns_sz = 0;
	int len;
	Pattern *_ignore = NULL;
	int ignore_sz = 0;
	PyObject *py_input = NULL;
	char *encoded_input = NULL;
	int encoded_input_sz = 0;

	self->scanner = NULL;

	if (!PyArg_ParseTuple(args, "OO|U", &patterns, &ignore, &py_input)) {
		return -1;
	}

	if (!Scanner_initialized()) {
		is_tuple = PyTuple_Check(patterns);
		if (is_tuple || PyList_Check(patterns)) {
			size = is_tuple ? PyTuple_Size(patterns) : PyList_Size(patterns);
			_patterns = PyMem_New(Pattern, size);
			for (i = 0; i < size; ++i) {
				item = is_tuple ? PyTuple_GetItem(patterns, i) : PyList_GetItem(patterns, i);
				_is_tuple = PyTuple_Check(item);
				if (_is_tuple || PyList_Check(item)) {
					item0 = _is_tuple ? PyTuple_GetItem(item, 0) : PyList_GetItem(item, 0);
					item1 = _is_tuple ? PyTuple_GetItem(item, 1) : PyList_GetItem(item, 1);
					if (PyUnicode_Check(item0) && PyUnicode_Check(item1)) {
						_patterns[patterns_sz].tok = scss_pyunicode_to_utf8(item0, &len);
						_patterns[patterns_sz].expr = scss_pyunicode_to_utf8(item1, &len);
						patterns_sz++;
					}
				}
			}
		}
		Scanner_initialize(_patterns, patterns_sz);
	}

	is_tuple = PyTuple_Check(ignore);
	if (is_tuple || PyList_Check(ignore)) {
		size = is_tuple ? PyTuple_Size(ignore) : PyList_Size(ignore);
		_ignore = PyMem_New(Pattern, size);
		for (i = 0; i < size; ++i) {
			item = is_tuple ? PyTuple_GetItem(ignore, i) : PyList_GetItem(ignore, i);
			if (PyUnicode_Check(item)) {
				_ignore[ignore_sz].tok = scss_pyunicode_to_utf8(item, &len);
				_ignore[ignore_sz].expr = NULL;
				ignore_sz++;
			}
		}
	}

	self->py_input = py_input;
	Py_INCREF(py_input);
	encoded_input = scss_pyunicode_to_utf8(py_input, &encoded_input_sz);
	self->scanner = Scanner_new(
		_patterns,
		patterns_sz,
		_ignore,
		ignore_sz,
		encoded_input,
		encoded_input_sz);

	if (_patterns != NULL) PyMem_Del(_patterns);
	if (_ignore != NULL) PyMem_Del(_ignore);

	#ifdef DEBUG
		PySys_WriteStderr("Scss Scanner object initialized! (%lu bytes)\n", sizeof(scss_Scanner));
	#endif

	return 0;
}

static PyObject *
scss_Scanner_repr(scss_Scanner *self)
{
	/* Print the last 10 tokens that have been scanned in */
	PyObject *repr, *tmp;
	Token *p_token;
	int i, start, pos;

	if (self->scanner != NULL && self->scanner->tokens_sz) {
		start = self->scanner->tokens_sz - 10;
		repr = PyBytes_FromString("");
		for (i = (start < 0) ? 0 : start; i < self->scanner->tokens_sz; i++) {
			p_token = &self->scanner->tokens[i];
			PyBytes_ConcatAndDel(&repr, PyBytes_FromString("\n"));
			pos = (int)(p_token->string - self->scanner->input);
			PyBytes_ConcatAndDel(&repr, PyBytes_FromFormat("  (@%d)  %s  =  ",
				pos, p_token->regex->tok));
			tmp = PyBytes_FromStringAndSize(p_token->string, p_token->string_sz);
			PyBytes_ConcatAndDel(&repr, PyObject_Repr(tmp));
			Py_XDECREF(tmp);
		}
	} else {
		repr = PyBytes_FromString("None");
	}

	return (PyObject *)repr;
}

static void
scss_Scanner_dealloc(scss_Scanner *self)
{
	if (self->scanner != NULL) Scanner_del(self->scanner);

	Py_XDECREF(self->py_input);

	Py_TYPE(self)->tp_free((PyObject*)self);

	#ifdef DEBUG
		PySys_WriteStderr("Scss Scanner object destroyed!\n");
	#endif
}

static PyMethodDef scss_Scanner_methods[] = {
	{"reset", (PyCFunction)scss_Scanner_reset, METH_VARARGS, "Scan the next token"},
	{"token", (PyCFunction)scss_Scanner_token, METH_VARARGS, "Get the nth token"},
	{"rewind", (PyCFunction)scss_Scanner_rewind, METH_VARARGS, "Rewind scanner"},
	{"setup_patterns", (PyCFunction)scss_Scanner_setup_patterns, METH_O | METH_STATIC, "Initialize patterns."},
	{NULL, NULL, 0, NULL}        /* Sentinel */
};

static PyTypeObject scss_ScannerType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"scss.Scanner",                            /* tp_name */
	sizeof(scss_Scanner),                      /* tp_basicsize */
	0,                                         /* tp_itemsize */
	(destructor)scss_Scanner_dealloc,          /* tp_dealloc */
	0,                                         /* tp_print */
	0,                                         /* tp_getattr */
	0,                                         /* tp_setattr */
	0,                                         /* tp_compare */
	(reprfunc)scss_Scanner_repr,               /* tp_repr */
	0,                                         /* tp_as_number */
	0,                                         /* tp_as_sequence */
	0,                                         /* tp_as_mapping */
	0,                                         /* tp_hash  */
	0,                                         /* tp_call */
	0,                                         /* tp_str */
	0,                                         /* tp_getattro */
	0,                                         /* tp_setattro */
	0,                                         /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,  /* tp_flags */
	"Scanner object.",                         /* tp_doc */
	0,                                         /* tp_traverse */
	0,                                         /* tp_clear */
	0,                                         /* tp_richcompare */
	0,                                         /* tp_weaklistoffset */
	0,                                         /* tp_iter: __iter__() method */
	0,                                         /* tp_iternext: next() method */
	scss_Scanner_methods,                      /* tp_methods */
	0,                                         /* tp_members */
	0,                                         /* tp_getset */
	0,                                         /* tp_base */
	0,                                         /* tp_dict */
	0,                                         /* tp_descr_get */
	0,                                         /* tp_descr_set */
	0,                                         /* tp_dictoffset */
	(initproc)scss_Scanner_init,               /* tp_init */
};


/* Python constructor */

static PyObject *
scss_locate_blocks(PyObject *self, PyObject *args)
{
	scss_BlockLocator *result = NULL;

	result = PyObject_New(scss_BlockLocator, &scss_BlockLocatorType);
	if (result) {
		scss_BlockLocator_init(result, args, NULL);
	}

	return (PyObject *)result;
}


/* Module functions */

static PyMethodDef scss_methods[] = {
	{"locate_blocks", (PyCFunction)scss_locate_blocks, METH_VARARGS, "Locate Scss blocks."},
	{NULL, NULL, 0, NULL}        /* Sentinel */
};

#if PY_MAJOR_VERSION >= 3

/* Module definition */

static struct PyModuleDef speedups_module_def = {
    PyModuleDef_HEAD_INIT,
    "_scanner",          /* m_name */
    NULL,                /* m_doc */
    (Py_ssize_t) -1,     /* m_size */
    scss_methods,        /* m_methods */
    NULL,                /* m_reload */
    NULL,                /* m_traverse */
    NULL,                /* m_clear */
    NULL,                /* m_free */
};

#endif

/* Module init function */

#if PY_MAJOR_VERSION >= 3
    #define MOD_INIT(name) PyMODINIT_FUNC PyInit_##name(void)
#else
    #define MOD_INIT(name) PyMODINIT_FUNC init##name(void)
#endif

MOD_INIT(_scanner)
{
#if PY_MAJOR_VERSION >= 3
	PyObject* m = PyModule_Create(&speedups_module_def);
#else
	PyObject* m = Py_InitModule("_scanner", scss_methods);
#endif

	scss_BlockLocatorType.tp_new = PyType_GenericNew;
	scss_ScannerType.tp_new = PyType_GenericNew;
#if PY_MAJOR_VERSION >= 3
	if (PyType_Ready(&scss_BlockLocatorType) < 0 || PyType_Ready(&scss_ScannerType) < 0)
		return m;
#else
	if (PyType_Ready(&scss_BlockLocatorType) < 0 || PyType_Ready(&scss_ScannerType) < 0)
		return;
#endif

	BlockLocator_initialize();
	Scanner_initialize(NULL, 0);

	Py_INCREF(&scss_BlockLocatorType);
	PyModule_AddObject(m, "_BlockLocator", (PyObject *)&scss_BlockLocatorType);

	Py_INCREF(&scss_ScannerType);
	PyModule_AddObject(m, "Scanner", (PyObject *)&scss_ScannerType);

	PyExc_scss_NoMoreTokens = PyErr_NewException("_scanner.NoMoreTokens", NULL, NULL);
	Py_INCREF(PyExc_scss_NoMoreTokens);
	PyModule_AddObject(m, "NoMoreTokens", (PyObject *)PyExc_scss_NoMoreTokens);
#if PY_MAJOR_VERSION >= 3
    return m;
#endif
}
