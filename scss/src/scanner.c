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

#include "utils.h"

int Pattern_patterns_sz = 0;
int Pattern_patterns_bsz = 0;
Pattern *Pattern_patterns = NULL;
int Pattern_patterns_initialized = 0;

Pattern*
Pattern_regex(char *tok, char *expr) {
	int j;

	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif

	for (j = 0; j < Pattern_patterns_sz; j++) {
		if (strcmp(Pattern_patterns[j].tok, tok) == 0) {
			return &Pattern_patterns[j];
		}
	}
	if (expr) {
		if (j >= Pattern_patterns_bsz) {
			/* Needs to expand block */
			Pattern_patterns_bsz = Pattern_patterns_bsz + BLOCK_SIZE_PATTERNS;
			PyMem_Resize(Pattern_patterns, Pattern, Pattern_patterns_bsz);
		}
		Pattern_patterns[j].tok = tok;
		Pattern_patterns[j].expr = expr;
		Pattern_patterns[j].pattern = NULL;
		Pattern_patterns_sz = j + 1;
		return &Pattern_patterns[j];
	}
	return NULL;
}

static int
Pattern_match(Pattern *regex, char *string, int string_sz, int start_at, Token *p_token) {
	int options = PCRE_ANCHORED | PCRE_UTF8;
	const char *errptr;
	int ret, erroffset, ovector[3];
	pcre *p_pattern = regex->pattern;
	ovector[0] = ovector[1] = ovector[2] = 0;

	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif

	if (p_pattern == NULL) {
		#ifdef DEBUG
			fprintf(stderr, "\tpcre_compile %s\n", repr(regex->expr));
		#endif
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

static void Pattern_initialize(Pattern *, int);
static void Pattern_finalize(void);


static void
Pattern_initialize(Pattern *patterns, int patterns_sz) {
	int i;
	Pattern *regex;

	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif

	if (Pattern_patterns_initialized || !patterns_sz) {
		return;
	}

	for (i = 0; i < patterns_sz; i++) {
		regex = Pattern_regex(patterns[i].tok, patterns[i].expr);
		#ifdef DEBUG
		if (regex) {
			fprintf(stderr, "\tAdded regex pattern %s: %s\n", repr(regex->tok), repr(regex->expr));
		}
		#endif
	}

	Pattern_patterns_initialized = 1;
}

static void
Pattern_finalize(void) {
	int j;

	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif

	if (Pattern_patterns_initialized) {
		for (j = 0; j < Pattern_patterns_sz; j++) {
			PyMem_Del(Pattern_patterns[j].tok);
			PyMem_Del(Pattern_patterns[j].expr);
			if (Pattern_patterns[j].pattern != NULL) {
				pcre_free(Pattern_patterns[j].pattern);
			}
		}
		PyMem_Del(Pattern_patterns);
		Pattern_patterns = NULL;
		Pattern_patterns_sz = 0;
		Pattern_patterns_bsz = 0;
		Pattern_patterns_initialized = 0;
	}
}

/* Scanner */

Hashtable *Scanner_restrictions_cache = NULL;

static long
_Scanner_scan(Scanner *self, Hashtable *restrictions)
{
	Token best_token, *p_token;
	Restriction *p_restriction;
	Pattern *regex;
	size_t len;
	int j;

	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif

	while (1) {
		regex = NULL;
		best_token.regex = NULL;

		/* Search the patterns for a match, with earlier
		   tokens in the list having preference */
		for (j = 0; j < Pattern_patterns_sz; j++) {
			regex = &Pattern_patterns[j];
			#ifdef DEBUG
				fprintf(stderr, "\tTrying %s: %s at pos %d -> %s (%d/%d)\n", repr(regex->tok), repr(regex->expr), self->pos, repr(self->input), j, Pattern_patterns_sz);
			#endif

			/* First check to see if we're restricting to this token */
			if (restrictions != NULL) {
				len = strlen(regex->tok) + 1;
				if (Hashtable_get(self->ignore, regex->tok, len) == NULL) {
					if (Hashtable_get(restrictions, regex->tok, len) == NULL) {
						#ifdef DEBUG
							fprintf(stderr, "\tSkipping %s!\n", repr(regex->tok));
						#endif
						continue;
					}
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
					fprintf(stderr, "Match OK! %s: %s at pos %d\n", repr(regex->tok), repr(regex->expr), self->pos);
				#endif
				break;
			}
		}

		/* If we didn't find anything, raise an error */
		if (best_token.regex == NULL) {
			if (restrictions) {
				return SCANNER_EXC_RESTRICTED;
			}
			return SCANNER_EXC_BAD_TOKEN;
		}

		/* If we found something that isn't to be ignored, return it */
		len = strlen(best_token.regex->tok) + 1;
		if (Hashtable_get(self->ignore, best_token.regex->tok, len) == NULL) {
			break;
		}

		/* This token should be ignored... */
		self->pos += best_token.string_sz;
	}

	if (best_token.regex) {
		self->pos = (int)(best_token.string - self->input + best_token.string_sz);
		/* Only add this token if it's not in the list (to prevent looping) */
		p_token = &self->tokens[self->tokens_sz - 1];
		if (self->tokens_sz == 0 ||
			p_token->regex != best_token.regex ||
			p_token->string != best_token.string ||
			p_token->string_sz != best_token.string_sz
		) {
			if (self->tokens_sz >= self->tokens_bsz) {
				/* Needs to expand block */
				self->tokens_bsz = self->tokens_bsz + BLOCK_SIZE_TOKENS;
				PyMem_Resize(self->tokens, Token, self->tokens_bsz);
				PyMem_Resize(self->restrictions, Restriction, self->tokens_bsz);
			}
			memcpy(&self->tokens[self->tokens_sz], &best_token, sizeof(Token));
			p_restriction = &self->restrictions[self->tokens_sz];
			p_restriction->patterns = restrictions;
			self->tokens_sz++;
			return 1;
		}
	}
	return 0;
}


/* Scanner public interface */

void
Scanner_reset(Scanner *self, char *input, int input_sz) {
	int i;

	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif

	for (i = 0; i < self->tokens_sz; i++) {
		self->restrictions[i].patterns = NULL;  /* patterns object is cached in self->patterns, and those are never deleted. */
	}
	self->tokens_sz = 0;

	if (self->input != NULL) {
		PyMem_Del(self->input);
	}
	self->input = input;
	self->input_sz = input_sz;
	#ifdef DEBUG
		fprintf(stderr, "Scanning in %s\n", repr(self->input));
	#endif

	self->pos = 0;
}

void
Scanner_del(Scanner *self) {
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif

	if (self->ignore != NULL) {
		Hashtable_del(self->ignore);
	}

	if (self->tokens != NULL) {
		PyMem_Del(self->tokens);
		PyMem_Del(self->restrictions);
	}

	if (self->input != NULL) {
		PyMem_Del(self->input);
	}

	PyMem_Del(self);
}

Scanner*
Scanner_new(Pattern patterns[], int patterns_sz, Pattern ignore[], int ignore_sz, char *input, int input_sz)
{
	int i;
	size_t len;
	Scanner *self;
	Pattern *regex;

	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif

	self = PyMem_New(Scanner, 1);
	memset(self, 0, sizeof(Scanner));
	if (self) {
		/* Restrictions cache */
		self->restrictions_cache = Scanner_restrictions_cache;
		/* Initialize patterns */
		for (i = 0; i < patterns_sz; i++) {
			regex = Pattern_regex(patterns[i].tok, patterns[i].expr);
			#ifdef DEBUG
			if (regex) {
				fprintf(stderr, "\tAdded regex pattern %s: %s\n", repr(regex->tok), repr(regex->expr));
			}
			#endif
		}
		/* Initialize ignored */
		if (ignore_sz) {
			self->ignore = Hashtable_create(64);
			for (i = 0; i < ignore_sz; i++) {
				regex = Pattern_regex(ignore[i].tok, ignore[i].expr);
				if (regex) {
					len = strlen(ignore[i].tok) + 1;
					Hashtable_set(self->ignore, ignore[i].tok, len, regex);
					#ifdef DEBUG
						fprintf(stderr, "\tIgnoring token %s\n", repr(regex->tok));
					#endif
				}
			}
		} else {
			self->ignore = NULL;
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

	Scanner_restrictions_cache = Hashtable_create(64);
	Pattern_initialize(patterns, patterns_sz);
}

void
Scanner_finalize(void)
{
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif

	Pattern_finalize();
	Hashtable_del(Scanner_restrictions_cache);

}

Token*
Scanner_token(Scanner *self, int i, Hashtable *restrictions)
{
	long result;

	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif

	if (i == self->tokens_sz) {
		result = _Scanner_scan(self, restrictions);
		if (result < 0) {
			return (Token *)result;
		}
	} else if (i >= 0 && i < self->tokens_sz) {
		if (!Hashtable_in(restrictions, self->restrictions[i].patterns)) {
			sprintf(self->exc, "Unimplemented: restriction set changed");
			return (Token *)SCANNER_EXC_UNIMPLEMENTED;
		}
	}
	if (i >= 0 && i < self->tokens_sz) {
		return &self->tokens[i];
	}
	return (Token *)SCANNER_EXC_NO_MORE_TOKENS;
}

void
Scanner_rewind(Scanner *self, int i)
{
	#ifdef DEBUG
		fprintf(stderr, "%s\n", __PRETTY_FUNCTION__);
	#endif

	if (i >= 0 && i < self->tokens_sz) {
		self->tokens_sz = i;
		self->pos = (int)(self->tokens[i].string - self->input);
	}
}
