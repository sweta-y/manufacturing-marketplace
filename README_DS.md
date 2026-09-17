# Data Structures in C — Manufacturing Marketplace

## 1. Priority Queue (Binary Min-Heap)
- **File:** `backend/c_module/priority_queue.c`
- **Problem solved:** Manufacturer ke available-requests list ko urgency (`estimated_days`, wait time, quantity) ke hisaab se order karna, plain SQL `ORDER BY` ki jagah.
- **Operations:** `heap_push` (insert, O(log n)), `heap_pop` (extract-min, O(log n)), `sift_up`/`sift_down`
- **Complexity:** Build O(n log n) for n requests, Space O(n)
- **Called from:** `backend/app/services/priority_service.py` -> `order_requests_by_priority()` -> `backend/app/routes/manufacturer_routes.py` (`available_requests` route)
- **Fallback:** Python sort (`estimated_days ASC`, `created_at ASC`) agar binary missing/fail ho, UI mein warning banner dikhta hai (`used_fallback` flag).

## 2. Hash Table (Separate Chaining)
- **File:** `backend/c_module/match_hash.c`
- **Problem solved:** Customer ke (process, material, quantity) request ko manufacturer machine capabilities ke against match karna, SQL `JOIN` ki jagah O(1) average lookup se.
- **Operations:** `insert` (O(1)), `lookup`/`query` (O(1) average, O(k) worst-case chain length)
- **Hash function:** `process_id` aur `material_id` ko combine karke bucket index.
- **Complexity:** Build O(M) for M capabilities, Query O(1) average
- **Called from:** `backend/app/services/matching_service.py` -> `find_matching_manufacturers_via_hash()` -> `customer_routes.py` (`upload_matches` step)
- **Fallback:** Original SQL-JOIN version (`find_matching_manufacturers`), verified functionally equivalent (test results identical dono cases mein).

## 3. Linked List (Circular Buffer)
- **File:** `backend/c_module/notif_ring.c`
- **Problem solved:** Har user ke recent N notifications ka fast in-memory view rakhna. DB hi source of truth rehti hai; ye sirf recent-view cache hai.
- **Operations:** `push` (O(1), capacity par oldest node evict), `get_recent` (O(k))
- **Data structure:** Singly linked list, **NOT array** — real node/pointer implementation.
- **Complexity:** Space O(capacity), not O(all notifications)
- **Called from:** `backend/app/services/notification_service.py` -> `get_recent_notifications_via_ring()`
- **Fallback:** SQL-based recent-notifications query.

## Common pattern across all three
- Har C binary independent standalone program hai, stdin se input leta hai, stdout pe result deta hai (koi shared library/FFI complexity nahi).
- Har ek ka Python fallback hai jo binary fail hone par activate hota hai, aur `used_fallback` flag se track hota hai.
- **Build:** `backend/c_module/Makefile` (single `make` command se sab compile).

## Known environment gotcha (for setup on a new machine)
- Windows par Smart App Control (agar Evaluation/On mode mein ho) unsigned GCC-built `.exe` files ko block kar sakta hai. Fix: **Settings > Privacy & security > Windows Security > App & browser control > Smart App Control > Off**, phir restart.