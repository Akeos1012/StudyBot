**Cache Memory** - A small, very fast type of memory located inside or very close to the **[[CPU]]**. It stores frequently used data and instructions so the CPU can access them quickly without repeatedly going to slower **[RAM]]**.

___
#### Why it exists? 

The CPU is extremely fast, but RAM is slower. Without cache, the CPU would waste time waiting for data.

**Cache solves this by:**
- keeping important data close to the CPU
- reducing delay (latency)
- improving overall performance

___
#### How it works?

1. CPU needs data
2. It first checks **cache memory**
3. If found → **Cache Hit (fast access)**
4. If not found → **Cache Miss (go to RAM)**
5. Data is then stored in cache for future use

___
#### Levels of Cache

- **L1 Cache** → smallest, fastest, inside CPU core
- **L2 Cache** → larger, slightly slower
- **L3 Cache** → shared between CPU cores, larger but slower than L1/L2

In short, Cache memory is a small, ultra-fast memory that stores frequently used [[Data]] to speed up CPU performance by reducing access time to RAM.