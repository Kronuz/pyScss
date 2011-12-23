#include <Python.h>

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

void reprl(char *str, int len) {
	char c,
		 *begin = str,
		 *end = str + len;
	PySys_WriteStdout("'");
	while (begin < end) {
		c = *begin;
		if (len == -1 && !c) {
			break;
		} else if (c == '\r') {
			PySys_WriteStdout("\\r");
		} else if (c == '\n') {
			PySys_WriteStdout("\\n");
		} else if (c == '\t') {
			PySys_WriteStdout("\\t");
		} else if (c < ' ') {
			PySys_WriteStdout("\\x%02x", c);
		} else {
			PySys_WriteStdout("%c", c);
		}
		begin++;
	}
	PySys_WriteStdout("'\n");
}
void repr(char *str, char *str2) {
	reprl(str, (int)(str2 - str));
}

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
				if (addnl && write != NULL) {
					*write++ = '\n';
				}
				if (write != NULL) {
					while (first < last) {
						*write++ = *first++;
					}
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
		if (addnl && write != NULL) {
			*write++ = '\n';
		}
		if (write != NULL) {
			while (first < last) {
				*write++ = *first++;
			}
			*write = '\0';
		}
	}

	return cnt;
}


typedef void scss_Callback(scss_LocateBlocks*, scss_Block*);

void _start_string(scss_LocateBlocks *p, scss_Block *b) {
	// PySys_WriteStdout("_start_string\n");
	// A string starts
	p->instr = *(p->codestr_ptr);
}

void _end_string(scss_LocateBlocks *p, scss_Block *b) {
	// PySys_WriteStdout("_end_string\n");
	// A string ends (FIXME: needs to accept escaped characters)
	p->instr = 0;
}

void _start_parenthesis(scss_LocateBlocks *p, scss_Block *b) {
	// PySys_WriteStdout("_start_parenthesis\n");
	// parenthesis begins:
	p->par++;
	p->thin = NULL;
	p->safe = p->codestr_ptr + 1;
}

void _end_parenthesis(scss_LocateBlocks *p, scss_Block *b) {
	// PySys_WriteStdout("_end_parenthesis\n");
	p->par--;
}

void _flush_properties(scss_LocateBlocks *p, scss_Block *b) {
	// PySys_WriteStdout("_flush_properties\n");
	// Flush properties
	int len, lineno = -1;
	if (p->lose < p->init) {
		len = _strip(p->lose, p->init, &lineno);
		if (len) {
			if (lineno != -1) {
				p->lineno = lineno;
			}

			b->selprop = p->lose;
			b->selprop_sz = len;
			b->codestr = NULL;
			b->codestr_sz = 0;
			b->lineno = p->lineno;
			b->valid = 1;
		}
		p->lose = p->init;
	}
}

void _start_block1(scss_LocateBlocks *p, scss_Block *b) {
	// PySys_WriteStdout("_start_block1\n");
	// Start block:
	if (p->codestr_ptr > p->codestr && *(p->codestr_ptr - 1) == '#') {
		p->skip = 1;
	} else {
		p->start = p->codestr_ptr;
		if (p->thin != NULL && _strip(p->thin, p->codestr_ptr, NULL)) {
			p->init = p->thin;
		}
		_flush_properties(p, b);
		p->thin = NULL;
	}
	p->depth++;
}

void _start_block(scss_LocateBlocks *p, scss_Block *b) {
	// PySys_WriteStdout("_start_block\n");
	// Start block:
	p->depth++;
}

void _end_block1(scss_LocateBlocks *p, scss_Block *b) {
	// PySys_WriteStdout("_end_block1\n");
	// Block ends:
	int len, lineno = -1;
	p->depth--;
	if (!p->skip) {
		p->end = p->codestr_ptr;
		len = _strip(p->init, p->start, &lineno);
		if (lineno != -1) {
			p->lineno = lineno;
		}

		b->selprop = p->init;
		b->selprop_sz = len;
		b->codestr = (p->start + 1);
		b->codestr_sz = (int)(p->end - (p->start + 1));
		b->lineno = p->lineno;
		b->valid = 1;

		p->init = p->safe = p->lose = p->end + 1;
		p->thin = NULL;
	}
	p->skip = 0;
}

void _end_block(scss_LocateBlocks *p, scss_Block *b) {
	// PySys_WriteStdout("_end_block\n");
	// Block ends:
	p->depth--;
}

void _end_property(scss_LocateBlocks *p, scss_Block *b) {
	// PySys_WriteStdout("_end_property\n");
	// End of property (or block):
	int len, lineno = -1;
	p->init = p->codestr_ptr;
	if (p->lose < p->init) {
		len = _strip(p->lose, p->init, &lineno);
		if (len) {
			if (lineno != -1) {
				p->lineno = lineno;
			}

			b->selprop = p->lose;
			b->selprop_sz = len;
			b->codestr = NULL;
			b->codestr_sz = 0;
			b->lineno = p->lineno;
			b->valid = 1;
		}
		p->init = p->safe = p->lose = p->codestr_ptr + 1;
	}
	p->thin = NULL;
}

void _mark_safe(scss_LocateBlocks *p, scss_Block *b) {
	// PySys_WriteStdout("_mark_safe\n");
	// We are on a safe zone
	if (p->thin != NULL && _strip(p->thin, p->codestr_ptr, NULL)) {
		p->init = p->thin;
	}
	p->thin = NULL;
	p->safe = p->codestr_ptr + 1;
}

void _mark_thin(scss_LocateBlocks *p, scss_Block *b) {
	// PySys_WriteStdout("_mark_thin\n");
	// Step on thin ice, if it breaks, it breaks here
	if (p->thin != NULL && _strip(p->thin, p->codestr_ptr, NULL)) {
		p->init = p->thin;
		p->thin = p->codestr_ptr + 1;
	} else if (p->thin == NULL && _strip(p->safe, p->codestr_ptr, NULL)) {
		p->thin = p->codestr_ptr + 1;
	}
}


scss_Callback* scss_function_map[256 * 256 * 2 * 3]; // (c, instr, par, depth)
void init_function_map(void) {
	int i;
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
	// PySys_WriteStdout("Scss function maps initialized!\n");
}

PyObject* scss_LocateBlocks_iter(PyObject *self)
{
	Py_INCREF(self);
	return self;
}

PyObject* scss_LocateBlocks_iternext(PyObject *self)
{
	scss_Callback *fn;
	char c = 0;
	scss_Block b;
	scss_LocateBlocks *p = (scss_LocateBlocks *)self;
	char *codestr_end = p->codestr + p->codestr_sz;
	while (p->codestr_ptr < codestr_end) {
		c = *(p->codestr_ptr);
		if (!c) {
			p->codestr_ptr++;
			continue;
		}

		repeat:
		fn = scss_function_map[
			(int)c +
			256 * p->instr +
			256 * 256 * (int)(p->par != 0) +
			256 * 256 * 2 * (int)(p->depth > 1 ? 2 : p->depth)
		];

		b.valid = 0;

		if (fn != NULL) {
			fn(p, &b);
		}

		p->codestr_ptr++;
		if (p->codestr_ptr > codestr_end) {
			p->codestr_ptr = codestr_end;
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
	if (p->par > 0) {
		if (p->exc == NULL) p->exc = "Missing closing parenthesis somewhere in block";
	} else if (p->instr != 0) {
		if (p->exc == NULL) p->exc = "Missing closing string somewhere in block";
	} else if (p->depth > 0) {
		if (p->exc == NULL) p->exc = "Block never closed";
		if (p->init < codestr_end) {
			c = '}';
			goto repeat;
		}
	}
	if (p->lose < p->init) {
		c = 0;
		goto repeat;
	}

	if (p->exc) {
		PyErr_SetString(PyExc_Exception, p->exc);
	}

	/* Raising of standard StopIteration exception with empty value. */
	PyErr_SetNone(PyExc_StopIteration);
	return NULL;
}

static PyTypeObject scss_LocateBlocksType = {
	PyObject_HEAD_INIT(NULL)
	0,                         /*ob_size*/
	"scss._LocateBlocks",      /*tp_name*/
	sizeof(scss_LocateBlocks), /*tp_basicsize*/
	0,                         /*tp_itemsize*/
	0,                         /*tp_dealloc*/
	0,                         /*tp_print*/
	0,                         /*tp_getattr*/
	0,                         /*tp_setattr*/
	0,                         /*tp_compare*/
	0,                         /*tp_repr*/
	0,                         /*tp_as_number*/
	0,                         /*tp_as_sequence*/
	0,                         /*tp_as_mapping*/
	0,                         /*tp_hash */
	0,                         /*tp_call*/
	0,                         /*tp_str*/
	0,                         /*tp_getattro*/
	0,                         /*tp_setattro*/
	0,                         /*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_ITER,
	  /* tp_flags: Py_TPFLAGS_HAVE_ITER tells python to
		 use tp_iter and tp_iternext fields. */
	"Internal LocateBlocks iterator object.",      /* tp_doc */
	0,                         /* tp_traverse */
	0,                         /* tp_clear */
	0,                         /* tp_richcompare */
	0,                         /* tp_weaklistoffset */
	scss_LocateBlocks_iter,    /* tp_iter: __iter__() method */
	scss_LocateBlocks_iternext /* tp_iternext: next() method */
};

static PyObject *
scss_locate_blocks(PyObject *self, PyObject *args)
{
	char *codestr;
	int codestr_sz;
	scss_LocateBlocks *p;

	if (!PyArg_ParseTuple(args, "s#", &codestr, &codestr_sz))  return NULL;

	/* I don't need python callable __init__() method for this iterator,
	 so I'll simply allocate it as PyObject and initialize it by hand. */

	p = PyObject_New(scss_LocateBlocks, &scss_LocateBlocksType);
	if (!p) return NULL;

	/* I'm not sure if it's strictly necessary. */
	if (!PyObject_Init((PyObject *)p, &scss_LocateBlocksType)) {
		Py_DECREF(p);
		return NULL;
	}

	p->codestr = codestr;
	p->codestr_ptr = codestr;
	p->codestr_sz = codestr_sz;
	p->exc = NULL;
	p->lineno = 0;
	p->par = 0;
	p->instr = 0;
	p->depth = 0;
	p->skip = 0;
	p->thin = codestr;
	p->init = codestr;
	p->safe = codestr;
	p->lose = codestr;
	p->start = NULL;
	p->end = NULL;

	return (PyObject *)p;
}

static PyMethodDef scssMethods[] = {
	{"locate_blocks",  scss_locate_blocks, METH_VARARGS, "Locate Scss blocks."},
	{NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
init_scss(void)
{
	init_function_map();

	PyObject* m;

	scss_LocateBlocksType.tp_new = PyType_GenericNew;
	if (PyType_Ready(&scss_LocateBlocksType) < 0)  return;

	m = Py_InitModule("_scss", scssMethods);

	Py_INCREF(&scss_LocateBlocksType);
	PyModule_AddObject(m, "_LocateBlocks", (PyObject *)&scss_LocateBlocksType);
}

int
main(int argc, char *argv[])
{
	/* Pass argv[0] to the Python interpreter */
	Py_SetProgramName(argv[0]);

	/* Initialize the Python interpreter.  Required. */
	Py_Initialize();

	/* Add a static module */
	init_scss();

	return 0;
}
