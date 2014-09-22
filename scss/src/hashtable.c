/*
* [https://gist.github.com/tonious/1377667]
*
* Public Domain Hashtable
* Copyright (c) 2011 Tony Thompson (tonious).
*/

#include <stdlib.h>
#include <stdio.h>
#include <limits.h>
#include <string.h>

#include "hashtable.h"

static unsigned int
murmurhash3(const void *key, const size_t len, const unsigned int seed) {
	/* MurmurHash3, by Austin Appleby, also in the public domain */

	const unsigned int c1 = 0xcc9e2d51;
	const unsigned int c2 = 0x1b873593;
	const unsigned int r1 = 15;
	const unsigned int r2 = 13;
	const unsigned int m = 5;
	const unsigned int n = 0xe6546b64;
	const unsigned char *tail;

	size_t i;
	unsigned int k;
	unsigned int k1 = 0;
	unsigned int hash = seed;

	const size_t nblocks = len / 4;
	const unsigned int *blocks = (const unsigned int *) key;


	for (i = 0; i < nblocks; i++) {
		k = blocks[i];
		k *= c1;
		k = (k << r1) | (k >> (32 - r1));
		k *= c2;

		hash ^= k;
		hash = ((hash << r2) | (hash >> (32 - r2))) * m + n;
	}

	tail = (const unsigned char *)(key + nblocks * 4);

	switch (len & 3) {
		case 3:
			k1 ^= tail[2] << 16;
		case 2:
			k1 ^= tail[1] << 8;
		case 1:
			k1 ^= tail[0];

			k1 *= c1;
			k1 = (k1 << r1) | (k1 >> (32 - r1));
			k1 *= c2;
			hash ^= k1;
	}

	hash ^= len;
	hash ^= (hash >> 16);
	hash *= 0x85ebca6b;
	hash ^= (hash >> 13);
	hash *= 0xc2b2ae35;
	hash ^= (hash >> 16);

	return hash;
}

Hashtable *
Hashtable_create(const unsigned int size) {
	/* Create a new hashtable */

	unsigned int i, map_size;
	Hashtable *hashtable = NULL;

	if (size < 1) return NULL;

	/* Allocate the table itself. */
	if ((hashtable = malloc(sizeof(Hashtable))) == NULL) {
		return NULL;
	}

	/* Allocate pointers to the head nodes. */
	if ((hashtable->table = malloc(sizeof(Entry *) * size)) == NULL) {
		return NULL;
	}
	for (i = 0; i < size; i++) {
		hashtable->table[i] = NULL;
	}

	map_size = (size + sizeof(unsigned long) - 1) / (8 * sizeof(unsigned long));
	if ((hashtable->map = malloc(map_size)) == NULL) {
		return NULL;
	}
	for (i = 0; i < map_size; i++) {
		hashtable->map[i] = 0;
	}

	hashtable->size = size;

	return hashtable;
}

void
Hashtable_del(Hashtable *hashtable) {
	int bin;
	Entry *next = NULL;
	Entry *last = NULL;

	for (bin = 0; bin < hashtable->size; bin++) {
		next = hashtable->table[bin];

		while (next != NULL) {
			last = next;
			next = next->next;
			if (last->key != NULL) {
				free(last->key);
			}
			free(last);
		}
	}
	free(hashtable->map);
	free(hashtable->table);
	free(hashtable);
}

static Entry *
_Hashtable_newpair(const void *key, const size_t len, void *value) {
	/* Create a key-value pair */

	Entry *newpair;

	if ((newpair = malloc(sizeof(Entry))) == NULL) {
		return NULL;
	}

	if ((newpair->key = memcpy(malloc(len), key, len)) == NULL) {
		return NULL;
	}

	newpair->value = value;

	newpair->next = NULL;

	return newpair;
}

int
Hashtable_in(Hashtable *a, Hashtable *b) {
	int i, map_size;

	if (a->size == b->size) {
		map_size = (a->size + sizeof(unsigned long) - 1) / (8 * sizeof(unsigned long));
		for (i = 0; i < map_size; i++) {
			if ((a->map[i] & b->map[i]) != a->map[i]) {
				return 0;
			}
		}
		return 1;
	}
	return 0;
}

void
Hashtable_set(Hashtable *hashtable, const void *key, const size_t len, void *value) {
	/* Insert a key-value pair into a hash table */

	unsigned int hash = murmurhash3(key, len, 0x9747b28c);

	Entry *newpair = NULL;
	Entry *next = NULL;
	Entry *last = NULL;

	unsigned int bin = hash % hashtable->size;

	hashtable->map[bin / (8 * sizeof(unsigned long))] |= bin % (8 * sizeof(unsigned long));

	next = hashtable->table[bin];

	while (next != NULL && next->key != NULL && memcmp(key, next->key, len) > 0) {
		last = next;
		next = next->next;
	}

	if( next != NULL && next->key != NULL && memcmp(key, next->key, len) == 0 ) {
		/* There's already a pair. Let's replace that value. */
		next->value = value;

	} else {
		/* Nope, could't find it. Time to grow a pair. */
		newpair = _Hashtable_newpair(key, len, value);

		/* We're at the start of the linked list in this bin. */
		if (next == hashtable->table[bin]) {
			newpair->next = next;
			hashtable->table[bin] = newpair;

		/* We're at the end of the linked list in this bin. */
		} else if (next == NULL) {
			last->next = newpair;

		/* We're in the middle of the list. */
		} else  {
			newpair->next = next;
			last->next = newpair;
		}
	}
}

void *
Hashtable_get(Hashtable *hashtable, const void *key, const size_t len) {
	/* Retrieve a key-value pair from a hash table */

	unsigned int hash = murmurhash3(key, len, 0x9747b28c);

	Entry *pair;

	unsigned int bin = hash % hashtable->size;

	/* Step through the bin, looking for our value. */
	pair = hashtable->table[bin];
	while (pair != NULL && pair->key != NULL && memcmp(key, pair->key, len) > 0) {
		pair = pair->next;
	}

	/* Did we actually find anything? */
	if (pair == NULL || pair->key == NULL || memcmp(key, pair->key, len) != 0) {
		return NULL;
	} else {
		return pair->value;
	}
}
