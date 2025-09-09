# Chapter 03: Storage and Retrieval - LSM-Tree Implementation

This project implements the storage and retrieval concepts from Chapter 3 of "Designing Data-Intensive Applications" by Martin Kleppmann. What started as a simple attempt to recreate the bash `db_set` and `db_get` examples turned into a deep dive into LSM-Trees, crash recovery, and the fundamental differences between stateless CLI tools and stateful database services.

## The Learning Journey

I began this project thinking I'd just implement the simple bash examples from DDIA and maybe add some sorting. What I ended up building was a fully functional LSM-Tree with Write-Ahead Logging that mirrors the architecture of production databases like Cassandra and LevelDB. Here's how that happened, and what I learned along the way.

## Journey Overview

### Phase 1: Simple Database (`db` command)
**Starting simple**: Just recreate those bash one-liners from the book.

```bash
# Simple append-only database
go run main.go db set mykey myvalue
go run main.go db get mykey
```

**How it works**:
- `db set`: Appends `key,value` to a file (just like `echo "$1,$2" >> database`)
- `db get`: Scans entire file linearly to find the latest value (like `grep "^$1," database | tail -n1`)

This was straightforward to implement and taught me the basics of append-only logs. The simplicity was appealing - writes are fast, and you get durability for free. But the performance problems became obvious quickly.

**Problems I hit**:
- O(n) read performance (scans entire file every time)
- File grows indefinitely with no compaction
- No crash safety beyond whatever the filesystem provides
- Duplicate keys pile up with no cleanup

I could immediately see why the book talks about more sophisticated approaches. This works for small datasets, but doesn't scale.

### Phase 2: File-based LSM-Tree Attempt (`lsm` command - initial)
**Exploring the constraints**: I wanted to see how far I could push a CLI-based LSM-Tree implementation.

```bash
go run main.go lsm set mykey myvalue  # Creates numbered SSTable files
go run main.go lsm get mykey         # Searches through files
```

Knowing that each CLI command would be a separate process, I implemented the LSM-Tree components to see what would work and what wouldn't:

- **Sorted in-memory memtable** with binary search insertion
- **Size-based flushing** to SSTable files (`sstables/sstable-0001.sst`, etc.)
- **Binary search within SSTable files** for efficient reads
- **Newest-to-oldest search order** for last-write-wins semantics

**The expected limitation**: As anticipated, the in-memory memtable was lost between CLI invocations. This meant:
- Only flushed data persisted between commands
- Recent writes vanished unless they triggered a flush
- No real in-memory performance benefits
- Essentially a sophisticated file-based storage system

While this confirmed what I already knew about stateless vs stateful services, it was valuable to implement the LSM-Tree data structures and see how they behaved in this constrained environment. The file-based components worked well, but the full LSM-Tree benefits required a persistent service.

### Phase 3: HTTP Server LSM-Tree (`lsm serve`)
**Building it properly**: Time to implement a real persistent LSM-Tree service.

```bash
# Start LSM server
go run main.go lsm serve --max-memtable-size=1000 --sstable-prefix=data

# Client operations (separate processes)
go run main.go lsm set mykey myvalue
go run main.go lsm get mykey
```

This was the fun part - building the architecture that would actually let the LSM-Tree shine:

**Architecture**:
- **Server**: Long-running process maintaining LSM-Tree state
- **Client**: CLI commands making HTTP requests to server  
- **HTTP API**: Clean RESTful endpoints (`POST /set`, `GET /get?key=...`)

**What I learned building this**:
- Request validation and error handling matter more in HTTP APIs
- Thread safety becomes critical with concurrent requests (hello mutexes!)
- Configurable parameters make testing so much easier
- The separation between client and server logic forces cleaner abstractions

**Benefits achieved**:
- True in-memory performance for recent data (memtable stays hot)
- Persistent server state across thousands of client requests
- Proper LSM-Tree behavior with memtable + SSTables working together
- Configurable memtable flush thresholds (essential for testing with small datasets)

The HTTP approach also made the system feel more like a real database - you start the service once, then multiple clients can interact with it. Much more realistic than the CLI-only approach.

### Phase 4: Write-Ahead Log (WAL) for Crash Recovery
**The durability problem**: Great, now I have a working LSM-Tree service, but what happens when it crashes?

Any data sitting in the memtable would be lost forever. This is unacceptable for a database - you can't just lose people's recent writes because the server went down.

**The WAL solution**: This is where I learned how real databases handle crash recovery.

**Write path** (durability first):
1. Write operation → WAL file (hit disk immediately for safety)
2. Add to in-memory memtable (fast access for reads)
3. When memtable full → flush to SSTable + clear WAL (cleanup)

**Recovery path** (rebuild state):
1. Server startup → replay WAL entries line by line
2. Reconstruct memtable state exactly as it was before crash
3. Continue normal operation like nothing happened

**Implementation insights**:
```go
// Every write goes to WAL first - fail fast if this doesn't work
func (lsm *LSMTree) Set(key, value string) error {
    if err := lsm.writeToWAL(key, value); err != nil {
        return err  // Don't even try memtable if WAL fails
    }
    lsm.memTable.insert(key, value)
    // ... check for flush
}

// On server startup - replay the journal
func (lsm *LSMTree) replayWAL() {
    // Read WAL file, replay each entry into memtable
    // WAL can have duplicates (same key updated multiple times)
    // That's fine - memtable handles overwrites correctly
}
```

**Key insight**: The WAL doesn't need to be sorted or deduplicated. It's just a chronological journal of operations. The memtable reconstruction naturally handles duplicates and maintains sorted order.

This was when the project started feeling like a "real" database engine. The crash recovery approach follows the same basic principles as production systems like PostgreSQL and Cassandra, though obviously much simpler.

## Final Architecture

### Data Structures
- **Sorted Memtable**: Binary search tree-like structure for O(log n) inserts/lookups
- **SSTables**: Immutable, sorted files on disk with binary search
- **WAL**: Sequential append-only log for durability

### Read Path
1. Check memtable (newest data)
2. Check SSTables newest → oldest
3. Binary search within each SSTable file

### Write Path  
1. Append to WAL (crash safety)
2. Insert into sorted memtable
3. Flush to SSTable when threshold reached
4. Clear WAL after successful flush

### Key Features Implemented
- ✅ Sorted data structures with binary search
- ✅ Size-based memtable flushing
- ✅ Crash recovery via WAL replay
- ✅ Last-write-wins semantics
- ✅ HTTP API for remote access
- ✅ Configurable parameters for testing
- ✅ Thread-safe operations with mutexes

## LSM-Tree vs Traditional B-Trees

**LSM-Tree advantages** (implemented here):
- Sequential writes (WAL + SSTable creation)
- Better write performance under heavy load
- Natural data compaction through flushing

**Trade-offs observed**:
- Read amplification (check multiple files)
- Background compaction needed (not implemented)
- More complex crash recovery

## Real-World Database Connections

This implementation mirrors the architecture used by:
- **Apache Cassandra**: LSM-Trees with memtables and SSTables
- **LevelDB/RocksDB**: Similar WAL + memtable + SSTable design
- **Apache HBase**: WAL for durability, in-memory stores for performance

## What I Learned About Database Storage Engines

**The power of hybrid approaches**: The combination of in-memory memtables and disk-based SSTables gives you the best of both worlds - fast writes, fast recent reads, and durability through persistence.

**Binary search is everywhere**: From memtable insertion to SSTable lookups, having sorted data unlocks O(log n) performance. The investment in maintaining sorted order pays dividends across all operations.

**Write-ahead logging is magical**: The WAL pattern solves the durability problem elegantly without sacrificing performance. Sequential writes to the WAL are fast, and you only pay the replay cost on crashes (which should be rare).

**Configuration matters for testing**: Making memtable size configurable (`--max-memtable-size=10`) made it trivial to test flush behavior without generating thousands of entries.

**Real databases are stateful services**: This seems obvious in hindsight, but building the CLI version first really hammered home why databases need to be long-running processes that maintain state.

**Last-write-wins is simple but effective**: Having multiple SSTables with potentially duplicate keys sounds inefficient, but the newest-first search strategy makes it work cleanly. Compaction can clean up duplicates later.

**Thread safety is non-negotiable**: Once you add HTTP endpoints, concurrent requests become a real concern. Mutexes around LSM operations were essential.

## Key Lessons from DDIA Chapter 3

1. **Storage engines matter**: LSM-Trees vs B-Trees isn't just academic - they have fundamentally different performance characteristics
2. **Durability vs Performance**: WAL provides crash safety without sacrificing write throughput
3. **Read amplification vs Write amplification**: LSM-Trees optimize for writes at the cost of more complex reads
4. **Crash recovery must be designed upfront**: Adding WAL later would have been much harder than building it in from the start
5. **Simplicity has limits**: The append-only log from the bash examples works great until you need performance

## Usage

```bash
# Start server with small memtable for testing
go run main.go lsm serve --max-memtable-size=10 --sstable-prefix=testdata

# In separate terminals:
go run main.go lsm set user123 alice
go run main.go lsm set user456 bob
go run main.go lsm get user123

# Test crash recovery:
# 1. Add some data (< 10 entries)
# 2. Kill server (Ctrl+C)
# 3. Restart server
# 4. Data should be recovered from WAL
```

## Files Generated
- `testdata/wal.log`: Write-ahead log for crash recovery
- `testdata/testdata-0001.sst`: SSTable files with sorted key-value pairs
- `testdata/testdata-0002.sst`: Additional SSTables as memtable flushes

## Reflections

What started as a simple exercise in recreating bash examples became a deep exploration of how modern databases actually work. The progression from append-only logs through file-based LSM attempts to a full service with crash recovery mirrors the real evolution of database storage engines.

The most valuable part wasn't just implementing the data structures - it was hitting the constraints and understanding *why* databases are architected the way they are. The CLI limitation forced me to really understand the difference between stateless operations and stateful services. The crash recovery requirement made WAL implementation essential rather than optional.

Building this gave me a much deeper appreciation for the engineering that goes into production databases. The concepts in DDIA Chapter 3 aren't just academic - they solve real problems that you encounter as soon as you try to build anything non-trivial.