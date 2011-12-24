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

/* Counter type */
staticforward PyTypeObject scss_LocateBlocksType;

#undef DEBUG

void reprl(char *str, int len) {
	char c,
		 *begin = str,
		 *end = str + len;
	PySys_WriteStderr("'");
	while (begin < end) {
		c = *begin;
		if (len == -1 && !c) {
			break;
		} else if (c == '\r') {
			PySys_WriteStderr("\\r");
		} else if (c == '\n') {
			PySys_WriteStderr("\\n");
		} else if (c == '\t') {
			PySys_WriteStderr("\\t");
		} else if (c < ' ') {
			PySys_WriteStderr("\\x%02x", c);
		} else {
			PySys_WriteStderr("%c", c);
		}
		begin++;
	}
	PySys_WriteStderr("'\n");
}
void repr(char *str, char *str2) {
	reprl(str, (int)(str2 - str));
}

typedef struct {
	PyObject_HEAD
	char *codestr;
	char *codestr_ptr;
	int codestr_sz;
	char *exc;
	int lineno;
	int par;
	char instr;
	int depth;
	int skip;
	char *thin;
	char *init;
	char *safe;
	char *lose;
	char *start;
	char *end;
} scss_LocateBlocks;


typedef struct {
	int valid;
	int lineno;
	char *selprop;
	int selprop_sz;
	char *codestr;
	int codestr_sz;
} scss_Block;


int _strip(char *begin, char *end, int *lineno) {
	// "    1\0     some,    \n  2\0 aca  "
	int _cnt,
		cnt = 0,
		pass = 1,
		addnl = 0;
	char c,
		*line = NULL,
		*first = begin,
		*last = begin,
		*write = lineno ? begin : NULL;
	while (begin < end) {
		c = *begin;
		if (c == '\0') {
			if (line == NULL) {
				line = first;
				if (lineno) {
					sscanf(line, "%d", lineno);
				}
			}
			first = last = begin + 1;
			pass = 1;
		} else if (c == '\n') {
			_cnt = (int)(last - first);
			if (_cnt > 0) {
				cnt += _cnt + addnl;
				if (write != NULL) {
					if (addnl) {
						*write++ = '\n';
					}
					while (first < last) {
						*write++ = *first++;
					}
					*write = '\0';
					addnl = 1;
				}
			}
			first = last = begin + 1;
			pass = 1;
		} else if (c == ' ' || c == '\t') {
			if (pass) {
				first = last = begin + 1;
			}
		} else {
			last = begin + 1;
			pass = 0;
		}
		begin++;
	}
	_cnt = (int)(last - first);
	if (_cnt > 0) {
		cnt += _cnt + addnl;
		if (write != NULL) {
			if (addnl) {
				*write++ = '\n';
			}
			while (first < last) {
				*write++ = *first++;
			}
			*write = '\0';
		}
	}

	return cnt;
}


typedef void scss_Callback(scss_LocateBlocks*, scss_Block*);


void _start_string(scss_LocateBlocks *self, scss_Block *b) {
	#ifdef DEBUG
		PySys_WriteStderr("_start_string\n");
	#endif
	// A string starts
	self->instr = *(self->codestr_ptr);
}

void _end_string(scss_LocateBlocks *self, scss_Block *b) {
	#ifdef DEBUG
		PySys_WriteStderr("_end_string\n");
	#endif
	// A string ends (FIXME: needs to accept escaped characters)
	self->instr = 0;
}

void _start_parenthesis(scss_LocateBlocks *self, scss_Block *b) {
	#ifdef DEBUG
		PySys_WriteStderr("_start_parenthesis\n");
	#endif
	// parenthesis begins:
	self->par++;
	self->thin = NULL;
	self->safe = self->codestr_ptr + 1;
}

void _end_parenthesis(scss_LocateBlocks *self, scss_Block *b) {
	#ifdef DEBUG
		PySys_WriteStderr("_end_parenthesis\n");
	#endif
	self->par--;
}

void _flush_properties(scss_LocateBlocks *self, scss_Block *b) {
	#ifdef DEBUG
		PySys_WriteStderr("_flush_properties\n");
	#endif
	// Flush properties
	int len, lineno = -1;
	if (self->lose <= self->init) {
		len = _strip(self->lose, self->init, &lineno);
		if (len) {
			if (lineno != -1) {
				self->lineno = lineno;
			}

			b->selprop = self->lose;
			b->selprop_sz = len;
			b->codestr = NULL;
			b->codestr_sz = 0;
			b->lineno = self->lineno;
			b->valid = 1;
		}
		self->lose = self->init;
	}
}

void _start_block1(scss_LocateBlocks *self, scss_Block *b) {
	#ifdef DEBUG
		PySys_WriteStderr("_start_block1\n");
	#endif
	// Start block:
	if (self->codestr_ptr > self->codestr && *(self->codestr_ptr - 1) == '#') {
		self->skip = 1;
	} else {
		self->start = self->codestr_ptr;
		if (self->thin != NULL && _strip(self->thin, self->codestr_ptr, NULL)) {
			self->init = self->thin;
		}
		_flush_properties(self, b);
		self->thin = NULL;
	}
	self->depth++;
}

void _start_block(scss_LocateBlocks *self, scss_Block *b) {
	#ifdef DEBUG
		PySys_WriteStderr("_start_block\n");
	#endif
	// Start block:
	self->depth++;
}

void _end_block1(scss_LocateBlocks *self, scss_Block *b) {
	#ifdef DEBUG
		PySys_WriteStderr("_end_block1\n");
	#endif
	// Block ends:
	int len, lineno = -1;
	self->depth--;
	if (!self->skip) {
		self->end = self->codestr_ptr;
		len = _strip(self->init, self->start, &lineno);
		if (lineno != -1) {
			self->lineno = lineno;
		}

		b->selprop = self->init;
		b->selprop_sz = len;
		b->codestr = (self->start + 1);
		b->codestr_sz = (int)(self->end - (self->start + 1));
		b->lineno = self->lineno;
		b->valid = 1;

		self->init = self->safe = self->lose = self->end + 1;
		self->thin = NULL;
	}
	self->skip = 0;
}

void _end_block(scss_LocateBlocks *self, scss_Block *b) {
	#ifdef DEBUG
		PySys_WriteStderr("_end_block\n");
	#endif
	// Block ends:
	self->depth--;
}

void _end_property(scss_LocateBlocks *self, scss_Block *b) {
	#ifdef DEBUG
		PySys_WriteStderr("_end_property\n");
	#endif
	// End of property (or block):
	int len, lineno = -1;
	self->init = self->codestr_ptr;
	if (self->lose <= self->init) {
		len = _strip(self->lose, self->init, &lineno);
		if (len) {
			if (lineno != -1) {
				self->lineno = lineno;
			}

			b->selprop = self->lose;
			b->selprop_sz = len;
			b->codestr = NULL;
			b->codestr_sz = 0;
			b->lineno = self->lineno;
			b->valid = 1;
		}
		self->init = self->safe = self->lose = self->codestr_ptr + 1;
	}
	self->thin = NULL;
}

void _mark_safe(scss_LocateBlocks *self, scss_Block *b) {
	#ifdef DEBUG
		PySys_WriteStderr("_mark_safe\n");
	#endif
	// We are on a safe zone
	if (self->thin != NULL && _strip(self->thin, self->codestr_ptr, NULL)) {
		self->init = self->thin;
	}
	self->thin = NULL;
	self->safe = self->codestr_ptr + 1;
}

void _mark_thin(scss_LocateBlocks *self, scss_Block *b) {
	#ifdef DEBUG
		PySys_WriteStderr("_mark_thin\n");
	#endif
	// Step on thin ice, if it breaks, it breaks here
	if (self->thin != NULL && _strip(self->thin, self->codestr_ptr, NULL)) {
		self->init = self->thin;
		self->thin = self->codestr_ptr + 1;
	} else if (self->thin == NULL && _strip(self->safe, self->codestr_ptr, NULL)) {
		self->thin = self->codestr_ptr + 1;
	}
}

int scss_function_map_initialized = 0;
scss_Callback* scss_function_map[256 * 256 * 2 * 3]; // (c, instr, par, depth)
void init_function_map(void) {
	int i;

	if (scss_function_map_initialized)
		return;
	scss_function_map_initialized = 1;

	for (i = 0; i < 256 * 256 * 2 * 3; i++) {
		scss_function_map[i] = NULL;
	}
	scss_function_map[(int)'\"' + 256*0 + 256*256*0 + 256*256*2*0] = _start_string;
	scss_function_map[(int)'\'' + 256*0 + 256*256*0 + 256*256*2*0] = _start_string;
	scss_function_map[(int)'\"' + 256*0 + 256*256*1 + 256*256*2*0] = _start_string;
	scss_function_map[(int)'\'' + 256*0 + 256*256*1 + 256*256*2*0] = _start_string;
	scss_function_map[(int)'\"' + 256*0 + 256*256*0 + 256*256*2*1] = _start_string;
	scss_function_map[(int)'\'' + 256*0 + 256*256*0 + 256*256*2*1] = _start_string;
	scss_function_map[(int)'\"' + 256*0 + 256*256*1 + 256*256*2*1] = _start_string;
	scss_function_map[(int)'\'' + 256*0 + 256*256*1 + 256*256*2*1] = _start_string;
	scss_function_map[(int)'\"' + 256*0 + 256*256*0 + 256*256*2*2] = _start_string;
	scss_function_map[(int)'\'' + 256*0 + 256*256*0 + 256*256*2*2] = _start_string;
	scss_function_map[(int)'\"' + 256*0 + 256*256*1 + 256*256*2*2] = _start_string;
	scss_function_map[(int)'\'' + 256*0 + 256*256*1 + 256*256*2*2] = _start_string;

	scss_function_map[(int)'\"' + 256*(int)'\"' + 256*256*0 + 256*256*2*0] = _end_string;
	scss_function_map[(int)'\'' + 256*(int)'\'' + 256*256*0 + 256*256*2*0] = _end_string;
	scss_function_map[(int)'\"' + 256*(int)'\"' + 256*256*1 + 256*256*2*0] = _end_string;
	scss_function_map[(int)'\'' + 256*(int)'\'' + 256*256*1 + 256*256*2*0] = _end_string;
	scss_function_map[(int)'\"' + 256*(int)'\"' + 256*256*0 + 256*256*2*1] = _end_string;
	scss_function_map[(int)'\'' + 256*(int)'\'' + 256*256*0 + 256*256*2*1] = _end_string;
	scss_function_map[(int)'\"' + 256*(int)'\"' + 256*256*1 + 256*256*2*1] = _end_string;
	scss_function_map[(int)'\'' + 256*(int)'\'' + 256*256*1 + 256*256*2*1] = _end_string;
	scss_function_map[(int)'\"' + 256*(int)'\"' + 256*256*0 + 256*256*2*2] = _end_string;
	scss_function_map[(int)'\'' + 256*(int)'\'' + 256*256*0 + 256*256*2*2] = _end_string;
	scss_function_map[(int)'\"' + 256*(int)'\"' + 256*256*1 + 256*256*2*2] = _end_string;
	scss_function_map[(int)'\'' + 256*(int)'\'' + 256*256*1 + 256*256*2*2] = _end_string;

	scss_function_map[(int)'(' + 256*0 + 256*256*0 + 256*256*2*0] = _start_parenthesis;
	scss_function_map[(int)'(' + 256*0 + 256*256*1 + 256*256*2*0] = _start_parenthesis;
	scss_function_map[(int)'(' + 256*0 + 256*256*0 + 256*256*2*1] = _start_parenthesis;
	scss_function_map[(int)'(' + 256*0 + 256*256*1 + 256*256*2*1] = _start_parenthesis;
	scss_function_map[(int)'(' + 256*0 + 256*256*0 + 256*256*2*2] = _start_parenthesis;
	scss_function_map[(int)'(' + 256*0 + 256*256*1 + 256*256*2*2] = _start_parenthesis;

	scss_function_map[(int)')' + 256*0 + 256*256*1 + 256*256*2*0] = _end_parenthesis;
	scss_function_map[(int)')' + 256*0 + 256*256*1 + 256*256*2*1] = _end_parenthesis;
	scss_function_map[(int)')' + 256*0 + 256*256*1 + 256*256*2*2] = _end_parenthesis;

	scss_function_map[(int)'{' + 256*0 + 256*256*0 + 256*256*2*0] = _start_block1;
	scss_function_map[(int)'{' + 256*0 + 256*256*0 + 256*256*2*1] = _start_block;
	scss_function_map[(int)'{' + 256*0 + 256*256*0 + 256*256*2*2] = _start_block;

	scss_function_map[(int)'}' + 256*0 + 256*256*0 + 256*256*2*1] = _end_block1;
	scss_function_map[(int)'}' + 256*0 + 256*256*0 + 256*256*2*2] = _end_block;

	scss_function_map[(int)';' + 256*0 + 256*256*0 + 256*256*2*0] = _end_property;

	scss_function_map[(int)',' + 256*0 + 256*256*0 + 256*256*2*0] = _mark_safe;

	scss_function_map[(int)'\n' + 256*0 + 256*256*0 + 256*256*2*0] = _mark_thin;

	scss_function_map[0 + 256*0 + 256*256*0 + 256*256*2*0] = _flush_properties;
	scss_function_map[0 + 256*0 + 256*256*0 + 256*256*2*1] = _flush_properties;
	scss_function_map[0 + 256*0 + 256*256*0 + 256*256*2*2] = _flush_properties;
	#ifdef DEBUG
		PySys_WriteStderr("Scss function maps initialized!\n");
	#endif
}


/* constructor */

static PyObject *
scss_LocateBlocks_new(char *codestr, int codestr_sz)
{
	scss_LocateBlocks *object;
	object = PyObject_New(scss_LocateBlocks, &scss_LocateBlocksType);

	if (object) {
		object->codestr = (char *)PyMem_Malloc(codestr_sz);
		memcpy(object->codestr, codestr, codestr_sz);
		object->codestr_ptr = object->codestr;
		object->codestr_sz = codestr_sz;
		object->exc = NULL;
		object->lineno = 0;
		object->par = 0;
		object->instr = 0;
		object->depth = 0;
		object->skip = 0;
		object->thin = object->codestr;
		object->init = object->codestr;
		object->safe = object->codestr;
		object->lose = object->codestr;
		object->start = NULL;
		object->end = NULL;
	}

	return (PyObject *)object;
}

static void
scss_LocateBlocks_dealloc(scss_LocateBlocks *self)
{
	PyMem_Free(self->codestr);
	self->ob_type->tp_free((PyObject*)self);
}


/*****/

scss_LocateBlocks*
scss_LocateBlocks_iter(scss_LocateBlocks *self)
{
	Py_INCREF(self);
	return self;
}

PyObject*
scss_LocateBlocks_iternext(scss_LocateBlocks *self)
{
	scss_Callback *fn;
	char c = 0;
	scss_Block b;
	char *codestr_end = self->codestr + self->codestr_sz;
	while (self->codestr_ptr < codestr_end) {
		c = *(self->codestr_ptr);
		if (!c) {
			self->codestr_ptr++;
			continue;
		}

		repeat:
		fn = scss_function_map[
			(int)c +
			256 * self->instr +
			256 * 256 * (int)(self->par != 0) +
			256 * 256 * 2 * (int)(self->depth > 1 ? 2 : self->depth)
		];

		b.valid = 0;

		if (fn != NULL) {
			fn(self, &b);
		}

		self->codestr_ptr++;
		if (self->codestr_ptr > codestr_end) {
			self->codestr_ptr = codestr_end;
		}

		if (b.valid) {
			return Py_BuildValue(
				"is#s#",
				b.lineno,
				b.selprop,
				b.selprop_sz,
				b.codestr,
				b.codestr_sz
			);
		}
	}
	if (self->par > 0) {
		if (self->exc == NULL) self->exc = "Missing closing parenthesis somewhere in block";
	} else if (self->instr != 0) {
		if (self->exc == NULL) self->exc = "Missing closing string somewhere in block";
	} else if (self->depth > 0) {
		if (self->exc == NULL) self->exc = "Block never closed";
		if (self->init < codestr_end) {
			c = '}';
			goto repeat;
		}
	}
	if (self->init < codestr_end) {
		self->init = codestr_end;
		c = 0;
		goto repeat;
	}

	if (self->exc) {
		PyErr_SetString(PyExc_Exception, self->exc);
		return NULL;
	}

	/* Raising of standard StopIteration exception with empty value. */
	PyErr_SetNone(PyExc_StopIteration);
	return NULL;
}


/* Type definition */

static PyTypeObject scss_LocateBlocksType = {
	PyObject_HEAD_INIT(NULL)
	0,                                         /* ob_size */
	"scss._LocateBlocks",                      /* tp_name */
	sizeof(scss_LocateBlocks),                 /* tp_basicsize */
	0,                                         /* tp_itemsize */
	(destructor)scss_LocateBlocks_dealloc,     /* tp_dealloc */
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
	"Internal LocateBlocks iterator object.",  /* tp_doc */
	0,                                         /* tp_traverse */
	0,                                         /* tp_clear */
	0,                                         /* tp_richcompare */
	0,                                         /* tp_weaklistoffset */
	(getiterfunc)scss_LocateBlocks_iter,       /* tp_iter: __iter__() method */
	(iternextfunc)scss_LocateBlocks_iternext,  /* tp_iternext: next() method */
};


/* Python constructor */

static PyObject *
scss_locate_blocks(PyObject *self, PyObject *args)
{
	PyObject *result = NULL;

	char *codestr;
	int codestr_sz;

	if (PyArg_ParseTuple(args, "s#", &codestr, &codestr_sz)) {
		result = scss_LocateBlocks_new(codestr, codestr_sz);
	}

	return result;
}


/* Module functions */

static PyMethodDef scssMethods[] = {
	{"locate_blocks",  scss_locate_blocks, METH_VARARGS, "Locate Scss blocks."},
	{NULL, NULL, 0, NULL}        /* Sentinel */
};


/* Module init function */

PyMODINIT_FUNC
init_scss(void)
{
	PyObject* m;

	scss_LocateBlocksType.tp_new = PyType_GenericNew;
	if (PyType_Ready(&scss_LocateBlocksType) < 0)
		return;

	m = Py_InitModule("_scss", scssMethods);

	init_function_map();

	Py_INCREF(&scss_LocateBlocksType);
	PyModule_AddObject(m, "_LocateBlocks", (PyObject *)&scss_LocateBlocksType);
}
