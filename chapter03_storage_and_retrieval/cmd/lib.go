package cmd

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"sync"
)

func dbSet(databaseFile, key, value string) error {
	file, err := os.OpenFile(databaseFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return fmt.Errorf("error opening file: %w", err)
	}
	defer file.Close()

	_, err = fmt.Fprintf(file, "%s,%s\n", key, value)
	if err != nil {
		return fmt.Errorf("error writing to file: %w", err)
	}
	return nil
}

func dbGet(databaseFile, key string) (string, error) {
	file, err := os.Open(databaseFile)
	if err != nil {
		if os.IsNotExist(err) {
			return "", fmt.Errorf("key not found")
		}
		return "", fmt.Errorf("error opening file: %w", err)
	}
	defer file.Close()
	scanner := bufio.NewScanner(file)
	var lastValue string
	found := false
	// Scan all lines to find the last occurrence of the key
	for scanner.Scan() {
		line := scanner.Text()
		parts := strings.SplitN(line, ",", 2)
		if len(parts) == 2 && parts[0] == key {
			lastValue = parts[1]
			found = true
		}
	}

	if err := scanner.Err(); err != nil {
		return "", fmt.Errorf("error reading file: %w", err)
	}

	if !found {
		return "", fmt.Errorf("key not found")
	}
	return lastValue, nil
}

type LSMServer struct {
	lsmTree *LSMTree
	mutex   sync.RWMutex // For thread safety
}

func startLSMServer(port, sstablePrefix string) {
	server := &LSMServer{
		lsmTree: NewLSMTree(1000, sstablePrefix),
	}

	http.HandleFunc("/set", server.handleSet)
	http.HandleFunc("/get", server.handleGet)

	fmt.Printf("LSM Server listening on port: %s\n", port)
	http.ListenAndServe(":"+port, nil)
}

func (s *LSMServer) handleSet(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		Key   string `json:"key"`
		Value string `json:"value"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		fmt.Printf("SET Request failed - invalid JSON: %v\n", err)
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate both key and value are provided
	if req.Key == "" {
		fmt.Printf("SET request failed - Missing key field\n")
		http.Error(w, "Missing key field", http.StatusBadRequest)
		return
	}
	if req.Value == "" {
		fmt.Printf("SET request failed - Missing value field\n")
		http.Error(w, "Missing value field", http.StatusBadRequest)
		return
	}

	fmt.Printf("SET request: key=%s value=%s\n", req.Key, req.Value)

	s.mutex.Lock()
	err := s.lsmTree.Set(req.Key, req.Value)
	s.mutex.Unlock()
	if err != nil {
		fmt.Printf("SET failed: %v\n", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	fmt.Printf("SET success: key=%s stored\n", req.Key)
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func (s *LSMServer) handleGet(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	key := r.URL.Query().Get("key")
	if key == "" {
		fmt.Printf("GET request failed - Missing key parameter\n")
		http.Error(w, "Missing key parameter", http.StatusBadRequest)
		return
	}

	fmt.Printf("GET request: key=%s\n", key)
	s.mutex.RLock()
	value, exists := s.lsmTree.Get(key)
	s.mutex.RUnlock()

	if !exists {
		fmt.Printf("GET failed: key=%s not found\n", key)
		http.Error(w, "Key not found", http.StatusNotFound)
		return
	}

	fmt.Printf("GET successs: key=%s, value=%s\n", key, value)
	json.NewEncoder(w).Encode(map[string]string{"value": value})
}

func makeHTTPSetRequest(serverURL, key, value string) error {
	reqBody := map[string]string{
		"key":   key,
		"value": value,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	resp, err := http.Post(serverURL+"/set", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("failed to make request: %w", err)
	}

	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("server error: %s", resp.Status)
	}
	return nil
}

func makeHTTPGetRequest(serverURL, key string) (string, error) {
	resp, err := http.Get(fmt.Sprintf("%s/get?key=%s", serverURL, key))
	if err != nil {
		return "", fmt.Errorf("failed to make request: %w", err)
	}

	defer resp.Body.Close()
	if resp.StatusCode == http.StatusNotFound {
		return "", fmt.Errorf("key not found")
	}
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("server error: %s", resp.Status)
	}

	var result map[string]string
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", fmt.Errorf("failed to decode response: %w", err)
	}

	return result["value"], nil
}

// Sorted Entry for Memtable
type Entry struct {
	Key   string
	Value string
}

// sorted memtable (slice kept sorted by key)
type SortedMemTable struct {
	entries []Entry
	size    int
}

// SS Table represents an immutable, sorted table
type SSTable struct {
	id      int     // unique identifier
	entries []Entry // sorted entries
	level   int     // which level this sstable belongs to
}

// true LSM-Tree structure
type LSMTree struct {
	memTable        *SortedMemTable
	sstables        map[int]*SSTable // Map of SSTable ID -> SSTable
	nextSSTableID   int
	maxMemTableSize int
	levels          [][]int // levels[i] = slice of SSTable IDs at level i
	sstablePrefix   string
	walPath         string
}

func NewLSMTree(maxMemTableSize int, sstablePrefix string) *LSMTree {
	walPath := fmt.Sprintf("%s/wal.log", sstablePrefix)
	lsm := &LSMTree{
		memTable: &SortedMemTable{
			entries: make([]Entry, 0),
			size:    0,
		},
		sstables:        make(map[int]*SSTable),
		nextSSTableID:   1,
		maxMemTableSize: maxMemTableSize,
		levels:          make([][]int, 10), // Support up to 10 levels
		sstablePrefix:   sstablePrefix,
		walPath:         walPath, // WAL is stored in the same directory
	}
	// replay WAL on startup to recover memtable
	lsm.replayWAL()
	return lsm
}

func (lsm *LSMTree) writeToWAL(key, value string) error {
	file, err := os.OpenFile(lsm.walPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return fmt.Errorf("failed to open WAL: %w", err)
	}
	defer file.Close()

	_, err = fmt.Fprintf(file, "%s,%s\n", key, value)
	if err != nil {
		return fmt.Errorf("failed to write to WAL: %w", err)
	}
	return nil
}

// Helper: Insert into sorted memtable
func (mt *SortedMemTable) insert(key, value string) {
	// Binary search for insertion point
	left, right := 0, len(mt.entries)
	for left < right {
		mid := (left + right) / 2
		if mt.entries[mid].Key < key {
			left = mid + 1
		} else {
			right = mid
		}
	}
	// Check if key already exists
	if left < len(mt.entries) && mt.entries[left].Key == key {
		mt.entries[left].Value = value // Update existing
	} else {
		// Insert new entry
		entry := Entry{Key: key, Value: value}
		mt.entries = append(mt.entries[:left], append([]Entry{entry}, mt.entries[left:]...)...)
		mt.size++
	}
}

func (mt *SortedMemTable) get(key string) (string, bool) {
	// Binary search
	left, right := 0, len(mt.entries)
	for left < right {
		mid := (left + right) / 2
		if mt.entries[mid].Key < key {
			left = mid + 1
		} else {
			right = mid
		}
	}

	if left < len(mt.entries) && mt.entries[left].Key == key {
		return mt.entries[left].Value, true
	}
	return "", false
}

func (lsm *LSMTree) flushMemTable() error {
	if lsm.memTable.size == 0 {
		return nil
	}

	// create the directory if needed
	if err := os.MkdirAll(lsm.sstablePrefix, 0755); err != nil {
		return fmt.Errorf("failed to create sst directory: %w", err)
	}
	// use prefix for filename
	filename := fmt.Sprintf("%s/%s-%04d.sst", lsm.sstablePrefix, lsm.sstablePrefix, lsm.nextSSTableID)

	file, err := os.Create(filename)
	if err != nil {
		return fmt.Errorf("failed to create SSTable: %w", err)
	}
	defer file.Close()

	// Write sorted entries to file
	for _, entry := range lsm.memTable.entries {
		_, err := fmt.Fprintf(file, "%s,%s\n", entry.Key, entry.Value)
		if err != nil {
			return fmt.Errorf("failed to write entry: %w", err)
		}
	}
	fmt.Printf("Flushed memtable to file: %s\n", filename)
	// clear memtable
	lsm.memTable.entries = make([]Entry, 0)
	lsm.memTable.size = 0
	lsm.nextSSTableID++
	// NOTE: Clear WAL after successful flush
	if err := lsm.clearWAL(); err != nil {
		fmt.Printf("Warning: failed to clear WAL: %v\n", err)
		// NOTE: We do not return an error here, the flush was successful.
	}
	return nil
}

// LSM-Tree Set method with flushing
func (lsm *LSMTree) Set(key, value string) error {
	// Write to WAL first (durability)
	if err := lsm.writeToWAL(key, value); err != nil {
		return err
	}
	// Insert into memtable
	lsm.memTable.insert(key, value)
	// Check if we need to flush
	if lsm.memTable.size >= lsm.maxMemTableSize {
		err := lsm.flushMemTable()
		if err != nil {
			return err
		}
	}
	return nil
}

// LSM-Tree Get method (checks memtable first, then SSTables)
func (lsm *LSMTree) Get(key string) (string, bool) {
	// Check memtable first
	if value, found := lsm.memTable.get(key); found {
		return value, true
	}
	// Check sstable files
	files := lsm.findSSTableFiles()
	for _, filename := range files {
		if value, found := lsm.searchSSTableFile(filename, key); found {
			return value, true
		}
	}
	return "", false
}

// Search for a key in a specific SSTableFile
func (lsm *LSMTree) searchSSTableFile(filename, key string) (string, bool) {
	file, err := os.Open(filename)
	if err != nil {
		return "", false // file can't be found or doesn't exist
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	lineCount := 0
	for scanner.Scan() {
		lineCount++
	}

	if lineCount == 0 {
		return "", false
	}

	// Binary search on line numbers
	left, right := 0, lineCount-1
	for left <= right {
		mid := (left + right) / 2
		// Seek back to the beginning and read to line 'mid'
		file.Seek(0, 0)
		scanner := bufio.NewScanner(file)
		// Skip to the mid line
		for i := 0; i < mid; i++ {
			scanner.Scan()
		}

		// Read the target line
		if !scanner.Scan() {
			break
		}
		line := scanner.Text()
		parts := strings.SplitN(line, ",", 2)
		if len(parts) != 2 {
			break
		}
		lineKey := parts[0]
		if lineKey < key {
			left = mid + 1
		} else if lineKey > key {
			right = mid - 1
		} else {
			// found it
			return parts[1], true
		}

	}
	return "", false
}

func (lsm *LSMTree) findSSTableFiles() []string {
	var files []string
	for i := 1; i < lsm.nextSSTableID; i++ {
		filename := fmt.Sprintf("%s/%s-%04d.sst", lsm.sstablePrefix, lsm.sstablePrefix, i)
		if _, err := os.Stat(filename); err == nil {
			files = append(files, filename)
		}
	}
	// return in reverse order, newest files first, remember?
	for i, j := 0, len(files)-1; i < j; i, j = i+1, j-1 {
		files[i], files[j] = files[j], files[i]
	}
	return files
}

func (lsm *LSMTree) replayWAL() {
	file, err := os.Open(lsm.walPath)
	if err != nil {
		// WAL doesn't exist yet, first startup
		return
	}
	defer file.Close()
	fmt.Printf("Replaying WAL from %s...\n", lsm.walPath)
	scanner := bufio.NewScanner(file)
	count := 0
	for scanner.Scan() {
		line := scanner.Text()
		parts := strings.SplitN(line, ",", 2)
		if len(parts) == 2 {
			lsm.memTable.insert(parts[0], parts[1])
			count++
		}
	}
	if count > 0 {
		fmt.Printf("Recovered %d entries from WAL\n", count)
	}
}

func (lsm *LSMTree) clearWAL() error {
	return os.Truncate(lsm.walPath, 0)
}
