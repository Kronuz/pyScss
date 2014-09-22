/*
* [https://gist.github.com/tonious/1377667]
*
* Public Domain Hashtable
* Copyright (c) 2011 Tony Thompson (tonious).
*/

#ifndef HASHTABLE_H
#define HASHTABLE_H

typedef struct Entry_s {
	char *key;
	void *value;
	struct Entry_s *next;
} Entry;

typedef struct {
	int size;
	Entry **table;
	unsigned long *map;
} Hashtable;

Hashtable *Hashtable_create(const unsigned int size);
void Hashtable_del(Hashtable *hashtable);
void Hashtable_set(Hashtable *hashtable, const void *key, const size_t len, void *value);
void *Hashtable_get(Hashtable *hashtable, const void *key, const size_t len);
int Hashtable_in(Hashtable *a, Hashtable *b);
#endif
