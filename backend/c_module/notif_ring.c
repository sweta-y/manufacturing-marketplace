/*
 * notif_ring.c
 * ------------------------------------------------------------------
 * Fixed-capacity circular buffer, implemented as a real singly linked
 * list of nodes (NOT an array) — used to hold each user's most recent
 * N notifications in memory. When full, the oldest node is evicted
 * (FIFO) to make room for the new one. This is a supplementary
 * "recent view" cache; the notifications table in PostgreSQL remains
 * the source of truth (this does not replace it).
 *
 * Push:        O(1) — append at tail; O(1) evict at head if full.
 * Get recent:  O(k) — walk k nodes from head (k <= CAPACITY).
 * Space:       O(CAPACITY) per user session, not O(all notifications).
 *
 * I/O protocol:
 *   stdin:
 *     CAPACITY
 *     N                                  (number of incoming pushes)
 *     notification_id created_at_epoch message_len
 *     message (message_len bytes, no embedded newline)
 *     ... (N times)
 *     K                                  (how many recent ones to return)
 *
 *   stdout:
 *     notification_id created_at_epoch message      (K lines, newest first)
 *
 * Build:
 *   gcc -O2 -Wall -o notif_ring notif_ring.c        (Linux/Mac)
 *   gcc -O2 -Wall -o notif_ring.exe notif_ring.c     (Windows/MinGW)
 * ------------------------------------------------------------------
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct Node {
    long notification_id;
    long created_at_epoch;
    char *message;
    struct Node *next;
} Node;

typedef struct {
    Node *head;   /* oldest */
    Node *tail;   /* newest */
    int size;
    int capacity;
} RingList;

static void ring_init(RingList *r, int capacity) {
    r->head = NULL;
    r->tail = NULL;
    r->size = 0;
    r->capacity = capacity;
}

/* Evict the oldest node (head). O(1). */
static void evict_oldest(RingList *r) {
    if (r->head == NULL) return;
    Node *old = r->head;
    r->head = old->next;
    if (r->head == NULL) {
        r->tail = NULL;
    }
    free(old->message);
    free(old);
    r->size--;
}

/* Push a new notification at the tail. If at capacity, evict the
 * oldest first (classic circular-buffer behaviour on a linked list). */
static void push(RingList *r, long id, long created_at, const char *message) {
    if (r->size == r->capacity) {
        evict_oldest(r);
    }
    Node *node = (Node *)malloc(sizeof(Node));
    node->notification_id = id;
    node->created_at_epoch = created_at;
    node->message = strdup(message);
    node->next = NULL;

    if (r->tail == NULL) {
        r->head = node;
        r->tail = node;
    } else {
        r->tail->next = node;
        r->tail = node;
    }
    r->size++;
}

/* Return the K most recent (newest first). We walk from tail backwards
 * is not possible in a singly linked list, so we collect head->tail
 * order into a small array and print in reverse. */
static void print_recent(RingList *r, int k) {
    if (k > r->size) k = r->size;
    Node **buf = (Node **)malloc(sizeof(Node *) * r->size);
    int i = 0;
    for (Node *cur = r->head; cur != NULL; cur = cur->next) {
        buf[i++] = cur;
    }
    /* buf[0..size-1] is oldest->newest; print last k in reverse (newest first) */
    for (int idx = r->size - 1; idx >= r->size - k; idx--) {
        printf("%ld %ld %s\n", buf[idx]->notification_id, buf[idx]->created_at_epoch, buf[idx]->message);
    }
    free(buf);
}

static void free_ring(RingList *r) {
    Node *cur = r->head;
    while (cur != NULL) {
        Node *tmp = cur;
        cur = cur->next;
        free(tmp->message);
        free(tmp);
    }
}

int main(void) {
    int capacity;
    if (scanf("%d", &capacity) != 1 || capacity <= 0) {
        fprintf(stderr, "{\"error\": \"invalid input: expected capacity\"}\n");
        return 1;
    }

    RingList ring;
    ring_init(&ring, capacity);

    int n;
    if (scanf("%d", &n) != 1 || n < 0) {
        fprintf(stderr, "{\"error\": \"invalid input: expected push count\"}\n");
        free_ring(&ring);
        return 1;
    }

    for (int i = 0; i < n; i++) {
        long id, created_at;
        int msg_len;
        if (scanf("%ld %ld %d", &id, &created_at, &msg_len) != 3) {
            fprintf(stderr, "{\"error\": \"invalid input: malformed push header %d\"}\n", i);
            free_ring(&ring);
            return 1;
        }
        char *message = (char *)malloc(msg_len + 2);
        /* consume the single whitespace/newline separator, then the message line */
        int c = getchar();
        (void)c;
        if (fgets(message, msg_len + 2, stdin) == NULL) {
            fprintf(stderr, "{\"error\": \"invalid input: malformed message %d\"}\n", i);
            free(message);
            free_ring(&ring);
            return 1;
        }
        size_t len = strlen(message);
        if (len > 0 && message[len - 1] == '\n') {
            message[len - 1] = '\0';
        }
        push(&ring, id, created_at, message);
        free(message);
    }

    int k;
    if (scanf("%d", &k) != 1 || k < 0) {
        fprintf(stderr, "{\"error\": \"invalid input: expected recent-count\"}\n");
        free_ring(&ring);
        return 1;
    }

    print_recent(&ring, k);

    free_ring(&ring);
    return 0;
}
