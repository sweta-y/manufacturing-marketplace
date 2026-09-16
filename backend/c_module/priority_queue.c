/*
 * priority_queue.c
 * ------------------------------------------------------------------
 * Real binary min-heap Priority Queue used to order a manufacturer's
 * "Available Requests" list by urgency instead of plain SQL ORDER BY.
 *
 * Priority key (lower = popped first = shown first):
 *   1. estimated_days   (fewer days left  -> more urgent)   [primary]
 *   2. wait_hours        (older request    -> more urgent)   [tie-break, negated]
 *   3. quantity           (bigger job       -> slightly more urgent) [tie-break, negated]
 *
 * A request with no estimated_days (-1 sent from Python) is treated as
 * the least urgent (LOW_PRIORITY_DAYS), so it still gets scheduled but
 * sinks to the bottom.
 *
 * I/O protocol (kept deliberately simple/text based so Python does not
 * need any C struct packing):
 *
 *   stdin:
 *     N
 *     order_id estimated_days wait_hours quantity      (N lines)
 *
 *   stdout (on success):
 *     order_id                                          (N lines, in
 *                                                         priority order)
 *
 * Exit code 0 on success, 1 on malformed input.
 *
 * Build:
 *   gcc -O2 -Wall -o priority_queue priority_queue.c       (Linux/Mac)
 *   gcc -O2 -Wall -o priority_queue.exe priority_queue.c   (Windows/MinGW)
 * or just `make` (see Makefile) which builds the right one for you.
 * ------------------------------------------------------------------
 */

#include <stdio.h>
#include <stdlib.h>

#define LOW_PRIORITY_DAYS 100000

typedef struct {
    long order_id;
    double priority_key; /* lower = more urgent, pops first */
    int estimated_days;
    double wait_hours;
    int quantity;
} PQNode;

typedef struct {
    PQNode *data;
    int size;
    int capacity;
} MinHeap;

static void heap_init(MinHeap *h, int capacity) {
    h->data = (PQNode *)malloc(sizeof(PQNode) * capacity);
    h->size = 0;
    h->capacity = capacity;
}

static void heap_swap(PQNode *a, PQNode *b) {
    PQNode tmp = *a;
    *a = *b;
    *b = tmp;
}

/* Percolate the newly inserted element (at the end) up until the
 * min-heap property (parent.key <= child.key) holds again. */
static void sift_up(MinHeap *h, int idx) {
    while (idx > 0) {
        int parent = (idx - 1) / 2;
        if (h->data[parent].priority_key <= h->data[idx].priority_key) {
            break;
        }
        heap_swap(&h->data[parent], &h->data[idx]);
        idx = parent;
    }
}

/* Insert operation: O(log n). This is the classic heap-push. */
static void heap_push(MinHeap *h, PQNode node) {
    if (h->size == h->capacity) {
        h->capacity *= 2;
        h->data = (PQNode *)realloc(h->data, sizeof(PQNode) * h->capacity);
    }
    h->data[h->size] = node;
    sift_up(h, h->size);
    h->size++;
}

/* Restore heap property downward from idx after the root is replaced. */
static void sift_down(MinHeap *h, int idx) {
    while (1) {
        int left = 2 * idx + 1;
        int right = 2 * idx + 2;
        int smallest = idx;

        if (left < h->size && h->data[left].priority_key < h->data[smallest].priority_key) {
            smallest = left;
        }
        if (right < h->size && h->data[right].priority_key < h->data[smallest].priority_key) {
            smallest = right;
        }
        if (smallest == idx) {
            break;
        }
        heap_swap(&h->data[idx], &h->data[smallest]);
        idx = smallest;
    }
}

/* Extract-min operation: O(log n). This is the classic heap-pop. */
static PQNode heap_pop(MinHeap *h) {
    PQNode top = h->data[0];
    h->size--;
    h->data[0] = h->data[h->size];
    sift_down(h, 0);
    return top;
}

static double compute_priority_key(int estimated_days, double wait_hours, int quantity) {
    int days = estimated_days;
    if (days < 0) {
        days = LOW_PRIORITY_DAYS; /* unknown -> least urgent */
    }
    /* Primary: fewer days = smaller key = popped first.
     * Tie-break 1: longer wait should reduce the key a little (older first).
     * Tie-break 2: bigger quantity should reduce the key a tiny bit more. */
    double key = (double)days * 1000.0;
    key -= (wait_hours * 0.01);
    key -= ((double)quantity * 0.001);
    return key;
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n < 0) {
        fprintf(stderr, "{\"error\": \"invalid input: expected request count\"}\n");
        return 1;
    }

    MinHeap heap;
    heap_init(&heap, n > 0 ? n : 1);

    for (int i = 0; i < n; i++) {
        long order_id;
        int estimated_days;
        double wait_hours;
        int quantity;

        if (scanf("%ld %d %lf %d", &order_id, &estimated_days, &wait_hours, &quantity) != 4) {
            fprintf(stderr, "{\"error\": \"invalid input: malformed request row %d\"}\n", i);
            free(heap.data);
            return 1;
        }

        PQNode node;
        node.order_id = order_id;
        node.estimated_days = estimated_days;
        node.wait_hours = wait_hours;
        node.quantity = quantity;
        node.priority_key = compute_priority_key(estimated_days, wait_hours, quantity);

        heap_push(&heap, node);
    }

    /* Extract in priority order -> naturally yields a sorted sequence
     * (this is heapsort's extraction phase, applied as a live PQ). */
    while (heap.size > 0) {
        PQNode top = heap_pop(&heap);
        printf("%ld\n", top.order_id);
    }

    free(heap.data);
    return 0;
}