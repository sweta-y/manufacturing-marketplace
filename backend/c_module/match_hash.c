/*
 * match_hash.c
 * ------------------------------------------------------------------
 * Separate-chaining Hash Table used to match a customer's
 * (process_id, material_id, quantity) request against every machine
 * capability a manufacturer has — replacing the SQL JOIN version of
 * this lookup with an actual data structure.
 *
 * Build phase:  O(M) to insert M machine-capability rows.
 * Query phase:  O(1) average (O(k) worst case, k = chain length at
 *               that bucket) instead of scanning/joining M rows.
 *
 * I/O protocol:
 *   stdin:
 *     M
 *     process_id material_id manufacturer_profile_id machine_id max_quantity   (M lines)
 *     query_process_id query_material_id query_quantity                        (1 line)
 *
 *   stdout:
 *     manufacturer_profile_id machine_id      (one line per match, max_quantity >= query_quantity)
 *
 * Build:
 *   gcc -O2 -Wall -o match_hash match_hash.c        (Linux/Mac)
 *   gcc -O2 -Wall -o match_hash.exe match_hash.c     (Windows/MinGW)
 * ------------------------------------------------------------------
 */

#include <stdio.h>
#include <stdlib.h>

#define TABLE_SIZE 257  /* prime, keeps distribution decent for small M */

typedef struct CapNode {
    int process_id;
    int material_id;
    long manufacturer_profile_id;
    long machine_id;
    int max_quantity;
    struct CapNode *next;   /* separate chaining */
} CapNode;

static CapNode *table[TABLE_SIZE];

/* Simple multiplicative hash combining two ids into one bucket index. */
static unsigned int hash_key(int process_id, int material_id) {
    unsigned int h = (unsigned int)process_id * 92821u + (unsigned int)material_id * 68917u;
    return h % TABLE_SIZE;
}

/* Insert: O(1) - prepend to the bucket's chain. */
static void insert(int process_id, int material_id, long mp_id, long machine_id, int max_qty) {
    unsigned int idx = hash_key(process_id, material_id);
    CapNode *node = (CapNode *)malloc(sizeof(CapNode));
    node->process_id = process_id;
    node->material_id = material_id;
    node->manufacturer_profile_id = mp_id;
    node->machine_id = machine_id;
    node->max_quantity = max_qty;
    node->next = table[idx];
    table[idx] = node;
}

/* Lookup: walk only the one bucket's chain, not all M rows. */
static void query(int process_id, int material_id, int quantity) {
    unsigned int idx = hash_key(process_id, material_id);
    CapNode *cur = table[idx];
    while (cur != NULL) {
        if (cur->process_id == process_id &&
            cur->material_id == material_id &&
            cur->max_quantity >= quantity) {
            printf("%ld %ld\n", cur->manufacturer_profile_id, cur->machine_id);
        }
        cur = cur->next;
    }
}

static void free_table(void) {
    for (int i = 0; i < TABLE_SIZE; i++) {
        CapNode *cur = table[i];
        while (cur != NULL) {
            CapNode *tmp = cur;
            cur = cur->next;
            free(tmp);
        }
    }
}

int main(void) {
    int m;
    if (scanf("%d", &m) != 1 || m < 0) {
        fprintf(stderr, "{\"error\": \"invalid input: expected capability count\"}\n");
        return 1;
    }

    for (int i = 0; i < m; i++) {
        int process_id, material_id, max_qty;
        long mp_id, machine_id;
        if (scanf("%d %d %ld %ld %d", &process_id, &material_id, &mp_id, &machine_id, &max_qty) != 5) {
            fprintf(stderr, "{\"error\": \"invalid input: malformed capability row %d\"}\n", i);
            free_table();
            return 1;
        }
        insert(process_id, material_id, mp_id, machine_id, max_qty);
    }

    int q_process, q_material, q_quantity;
    if (scanf("%d %d %d", &q_process, &q_material, &q_quantity) != 3) {
        fprintf(stderr, "{\"error\": \"invalid input: missing query line\"}\n");
        free_table();
        return 1;
    }

    query(q_process, q_material, q_quantity);

    free_table();
    return 0;
}
