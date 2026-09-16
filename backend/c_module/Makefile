CC ?= gcc
CFLAGS ?= -O2 -Wall

ifeq ($(OS),Windows_NT)
    EXT = .exe
else
    EXT =
endif

TARGETS = cost_estimator$(EXT) priority_queue$(EXT) match_hash$(EXT)

all: $(TARGETS)

cost_estimator$(EXT): cost_estimator.c
	$(CC) $(CFLAGS) -o $@ $< -lm

priority_queue$(EXT): priority_queue.c
	$(CC) $(CFLAGS) -o $@ $<

match_hash$(EXT): match_hash.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f $(TARGETS)
