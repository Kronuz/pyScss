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

#include <stdio.h>
#include <string.h>
#include "scanner.h"

char *
PyMem_Strdup(const char *str)
{
	if (str != NULL) {
		char *copy = PyMem_New(char, strlen(str) + 1);
		if (copy != NULL)
			return strcpy(copy, str);
	}
	return NULL;
}

Pattern *Pattern_patterns[MAX_PATTERNS];
int Pattern_patterns_initialized = 0;

Pattern*
Pattern_regex(char *tok, char *expr) {
	Pattern *ret = NULL;
	int j;
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif
	for (j = 0; j < MAX_PATTERNS; j++) {
		if(Pattern_patterns[j] == NULL) {
			if (expr) {
				Pattern_patterns[j] = PyMem_New(Pattern, 1);
				memset(Pattern_patterns[j], 0, sizeof(Pattern));
				Pattern_patterns[j]->tok = PyMem_Strdup(tok);
				Pattern_patterns[j]->expr = PyMem_Strdup(expr);
				ret = Pattern_patterns[j];
			}
			break;
		} else {
			if (strcmp(Pattern_patterns[j]->tok, tok) == 0) {
				ret = Pattern_patterns[j];
				break;
			}
		}
	}
	return ret;
}

static int
Pattern_match(Pattern *regex, char *string, int string_sz, int start_at, Token *p_token) {
	int options = PCRE_ANCHORED;
	const char *errptr;
	int ret, erroffset, ovector[3];
	pcre *p_pattern = regex->pattern;
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif
	if (p_pattern == NULL) {
		p_pattern = regex->pattern = pcre_compile(regex->expr, options, &errptr, &erroffset, NULL);
	}
	ret = pcre_exec(
		p_pattern,
		NULL,                  /* no extra data */
		string,
		string_sz,
		start_at,
		PCRE_ANCHORED,         /* default options */
		ovector,               /* output vector for substring information */
		3                      /* number of elements in the output vector */
	);
	if (ret >= 0) {
		if (p_token) {
			p_token->regex = regex;
			p_token->string = string + ovector[0];
			p_token->string_sz = ovector[1] - ovector[0];
		}
		return 1;
	}
	return 0;
}

static void Pattern_initialize(Pattern [], int);
static void Pattern_setup(Pattern [], int);
static void Pattern_finalize(void);


static void
Pattern_initialize(Pattern patterns[], int patterns_sz) {
	int j;
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif
	if (!Pattern_patterns_initialized) {
		for (j = 0; j < MAX_PATTERNS; j++) {
			Pattern_patterns[j] = NULL;
		}
		if (patterns_sz) {
			Pattern_patterns_initialized = 1;
			Pattern_setup(patterns, patterns_sz);
		}
	}
}

static void
Pattern_setup(Pattern patterns[], int patterns_sz) {
	int i;
	Pattern *regex;
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif
	if (!Pattern_patterns_initialized) {
		Pattern_initialize(patterns, patterns_sz);
	} else {
		for (i = 0; i < patterns_sz; i++) {
			regex = Pattern_regex(patterns[i].tok, patterns[i].expr);
			#ifdef DEBUG
			if (regex) {
				fprintf(stderr, "Added regex pattern '%s': '%s'\n", regex->tok, regex->expr);
			}
			#endif
		}
	}
}

static void
Pattern_finalize(void) {
	int j;
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif
	if (Pattern_patterns_initialized) {
		for (j = 0; j < MAX_PATTERNS; j++) {
			if (Pattern_patterns[j] != NULL) {
				PyMem_Del(Pattern_patterns[j]->tok);
				PyMem_Del(Pattern_patterns[j]->expr);
				if (Pattern_patterns[j]->pattern != NULL) {
					pcre_free(Pattern_patterns[j]->pattern);
				}
				PyMem_Del(Pattern_patterns[j]);
				Pattern_patterns[j] = NULL;
			}
		}
		Pattern_patterns_initialized = 0;
	}
}

/* Scanner */


static int
_Scanner_scan(Scanner *self, Pattern restrictions[], int restrictions_sz)
{
	Token best_token, *p_token;
	int j, k, max, skip;
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif
	while (1) {
		best_token.regex = NULL;
		/* Search the patterns for a match, with earlier
		   tokens in the list having preference */
		for (j = 0; j < MAX_PATTERNS; j++) {
			Pattern *regex = Pattern_patterns[j];
			if (regex == NULL) {
				break;
			}
			#ifdef DEBUG
			if (regex) {
				fprintf(stderr, "Trying '%s': '%s' at '%d' (\"%s\")\n", regex->tok, regex->expr, self->pos, self->input);
			}
			#endif
			/* First check to see if we're restricting to this token */
			skip = restrictions_sz;
			if (skip) {
				max = (restrictions_sz > self->ignore_sz) ? restrictions_sz : self->ignore_sz;
				for (k = 0; k < max; k++) {
					if (k < restrictions_sz && regex == Pattern_regex(restrictions[k].tok, restrictions[k].expr)) {
						skip = 0;
						break;
					}
					if (k < self->ignore_sz && regex == self->ignore[k]) {
						skip = 0;
						break;
					}
				}
				if (skip) {
					continue;
					#ifdef DEBUG
					if (regex) {
						fprintf(stderr, "Skipping!\n");
					}
					#endif
				}
			}
			if (Pattern_match(
				regex,
				self->input,
				self->input_sz,
				self->pos,
				&best_token
			)) {
				#ifdef DEBUG
				if (regex) {
					fprintf(stderr, "Match OK! '%s': '%s' at '%d'\n", regex->tok, regex->expr, self->pos);
				}
				#endif
				break;
			}
		}
		/* If we didn't find anything, raise an error */
		if (best_token.regex == NULL) {
			if (restrictions_sz) {
				sprintf(self->exc, "SyntaxError[@ char %d: Trying to find one of the %d restricted tokens!]", self->pos, restrictions_sz);
				return SCANNER_EXC_RESTRICTED;
			}
			sprintf(self->exc, "SyntaxError[@ char %d: Bad Token!]", self->pos);
			return SCANNER_EXC_BAD_TOKEN;
		}
		/* If we found something that isn't to be ignored, return it */
		skip = 0;
		for (k = 0; k < self->ignore_sz; k++) {
			if (best_token.regex == self->ignore[k]) {
				/* This token should be ignored... */
				self->pos += best_token.string_sz;
				skip = 1;
				break;
			}
		}
		if (!skip) {
			break;
		}
	}
	if (best_token.regex) {
		self->pos = (int)(best_token.string - self->input + best_token.string_sz);
		/* Only add this token if it's not in the list (to prevent looping) */
		if (self->tokens_sz == 0 ||
			self->tokens[self->tokens_sz - 1]->regex != best_token.regex ||
			self->tokens[self->tokens_sz - 1]->string != best_token.string ||
			self->tokens[self->tokens_sz - 1]->string_sz != best_token.string_sz
		) {
			p_token = (Token *)malloc(sizeof(Token));
			memcpy(p_token, &best_token, sizeof(Token));
			self->tokens[self->tokens_sz] = p_token;
			for (j = 0; j < MAX_PATTERNS; j++) {
				self->restrictions[self->tokens_sz][k] = (k < restrictions_sz) ? Pattern_regex(restrictions[k].tok, restrictions[k].expr) : NULL;
			}
			self->tokens_sz++;
			return 1;
		}
	}
	return 0;
}


/* Scanner public interface */

void
Scanner_reset(Scanner *self, char *input, int input_sz) {
	int i, j;
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif
	if (input_sz) {
		if (self->input) PyMem_Del(self->input);
		self->input = strndup(input, input_sz + 1);
		self->input[input_sz] = '\0';
		self->input_sz = input_sz;
	}
	self->tokens_sz = 0;
	for (i = 0; i < MAX_TOKENS; i++) {
		if (self->tokens[i]) {
			PyMem_Del(self->tokens[i]);
		}
		self->tokens[i] = NULL;
		for (j = 0; j < MAX_PATTERNS; j++) {
			self->restrictions[i][j] = NULL;
		}
		self->restrictions_sz[i] = 0;
	}
	self->pos = 0;
}

void
Scanner_del(Scanner *self) {
	int i;
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif
	for (i = 0; i < MAX_TOKENS; i++) {
		if (self->tokens[i]) {
			PyMem_Del(self->tokens[i]);
		}
		self->tokens[i] = NULL;
	}

	if (self->input != NULL) {
		PyMem_Del(self->input);
		self->input = NULL;
	}

	PyMem_Del(self);
}

Scanner*
Scanner_new(Pattern patterns[], int patterns_sz, Pattern ignore[], int ignore_sz, char *input, int input_sz)
{
	int i;
	Scanner *self;
	Pattern *regex;
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif
	self = PyMem_New(Scanner, 1);
	memset(self, 0, sizeof(Scanner));
	if (self) {
		for (i = 0; i < patterns_sz; i++) {
			regex = Pattern_regex(patterns[i].tok, patterns[i].expr);
			#ifdef DEBUG
			if (regex) {
				fprintf(stderr, "Added regex pattern '%s': '%s'\n", regex->tok, regex->expr);
			}
			#endif
		}
		for (i = 0; i < ignore_sz; i++) {
			regex = Pattern_regex(ignore[i].tok, ignore[i].expr);
			if (regex) {
				self->ignore[self->ignore_sz++] = regex;
				#ifdef DEBUG
					fprintf(stderr, "Ignoring token '%s'\n", regex->tok);
				#endif
			}
		}
		Scanner_reset(self, input, input_sz);
	}
	return self;
}

int
Scanner_initialized(void)
{
	return Pattern_patterns_initialized;
}

void
Scanner_initialize(Pattern patterns[], int patterns_sz)
{
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif
	Pattern_initialize(patterns, patterns_sz);
}

void
Scanner_finalize(void)
{
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif
	Pattern_finalize();
}


Token*
Scanner_token(Scanner *self, int i, Pattern restrictions[], int restrictions_sz)
{
	int j, k, found;
	Pattern *regex;
	int result;
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif
	if (i == self->tokens_sz) {
		result = _Scanner_scan(self, restrictions, restrictions_sz);
		if (result < 0) {
			return (Token *)result;
		}
	}
	if (i >= 0 && i < self->tokens_sz) {
		if (self->restrictions_sz[i]) {
			for (j = 0; j < restrictions_sz; j++) {
				found = 0;
				for (k = 0; k < self->restrictions_sz[i]; k++) {
					regex = Pattern_regex(restrictions[j].tok, restrictions[j].expr);
					if (regex == self->restrictions[i][k]) {
						found = 1;
						break;
					}
				}
				if (!found) {
					sprintf(self->exc, "Unimplemented: restriction set changed");
					return (Token *)SCANNER_EXC_UNIMPLEMENTED;
				}
			}
		}
		return self->tokens[i];
	}
	return (Token *)SCANNER_EXC_NO_MORE_TOKENS;
}

void
Scanner_rewind(Scanner *self, int i)
{
	Token *p_token;
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif
	if (i >= 0 && i < self->tokens_sz) {
		self->tokens_sz = i;
		p_token = self->tokens[i];
		self->pos = (int)(p_token->string - self->input);
	}
}
