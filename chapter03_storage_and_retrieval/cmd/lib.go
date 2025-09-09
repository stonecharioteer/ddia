package cmd
import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
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

	if err:= scanner.Err(); err != nil {
		return "", fmt.Errorf("error reading file: %w", err)
	}

	if !found {
		return "", fmt.Errorf("key not found")
	}
	return lastValue, nil
}


type MemTable map[string]string

type LSMTree struct {
	memTable MemTable
	sstables []string // path to the SSTable files
	memTableSize int // current size
	maxMemTableSize int // Flush threshold
}

// constructor
func NewLSMTree(maxMemTableSize int) *LSMTree {
	return &LSMTree{
		memTable: make(MemTable),
		sstables: []string{},
		memTableSize: 0,
		maxMemTableSize: maxMemTableSize,
	}
}

// simple set - just add to memory for now
func (lsm *LSMTree) Set(key, value, sstablePrefix string) error {
	lsm.memTable[key] = value
	lsm.memTableSize++
	// generate next numbered sstable file
	filename, err := lsm.generateNextSSTablePath(sstablePrefix)
	if err != nil {
		return err
	}
	return lsm.flushToSSTable(filename)
}

func (lsm *LSMTree) Get(key, sstablePrefix string) (string, error) {
	// Check Memtable first (will be empty since we flush immediately)
	if value, exists := lsm.memTable[key]; exists {
		return value, nil
	}
	// search through SSTables (newest first)
	sstableFiles, err := lsm.findSSTableFiles(sstablePrefix)
	if err != nil {
		return "", err
	}

	for _, filename := range sstableFiles {
		value, err := lsm.getFromSSTable(filename, key)
		if err == nil {
			return value, nil
		}
	}
	return "", fmt.Errorf("key not found")
}

func (lsm *LSMTree) flushToSSTable(filename string) error {
	if lsm.memTableSize == 0 {
		return nil // nothing to flush
	}
	file, err := os.OpenFile(filename, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return fmt.Errorf("error creating SSTable: %w", err)
	}
	defer file.Close()

	// Write sorted key-value pairs
	for key, value := range lsm.memTable {
		_, err = fmt.Fprintf(file, "%s,%s\n", key, value)
		if err != nil {
			return fmt.Errorf("error writing to SSTable: %w", err)
		}

	}
	// Clear memtable and add SSTable to list
	lsm.memTable = make(MemTable)
	lsm.memTableSize = 0
	lsm.sstables = append(lsm.sstables, filename)
	return nil
}

func (lsm *LSMTree) getFromSSTable(filename, key string) (string, error) {
	file, err := os.Open(filename)
	if err != nil {
		return "", fmt.Errorf("error reading SSTable file: %w", err)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	var lastValue string
	found := false

	for scanner.Scan() {
		line := scanner.Text()
		parts := strings.SplitN(line, ",", 2)
		if len(parts) == 2 && parts[0] == key {
			lastValue = parts[1]
			found = true
		}
	}

	if !found { 
		return "", fmt.Errorf("key not found")
	}
	return lastValue, nil

}

func (lsm *LSMTree) generateNextSSTablePath(prefix string) (string, error) {
	// create directory if it doesn't exist
	dir := filepath.Dir(prefix)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "", fmt.Errorf("failed to create directory: %w", err)
	}

	// find the next number by checking existing files
	counter := 1
	for {
		filename := fmt.Sprintf("%s-%04d.txt", prefix, counter)
		if _, err := os.Stat(filename); os.IsNotExist(err) {
			return filename, nil
		}
		counter++
	}

}

func (lsm *LSMTree) findSSTableFiles(prefix string) ([]string, error) {
	dir := filepath.Dir(prefix)
	baseName := filepath.Base(prefix)

	files, err := os.ReadDir(dir)
	if err != nil {
		if os.IsNotExist(err) {
			return []string{}, nil // Directory doesn't exist yet
		}
		return nil, fmt.Errorf("error reading directory: %w", err)
	}

	var sstableFiles []string
	for _, file := range files {
		if strings.HasPrefix(file.Name(), baseName+"-") && strings.HasSuffix(file.Name(), ".txt") {
			sstableFiles = append(sstableFiles, filepath.Join(dir, file.Name()))
		}
	}

	sort.Slice(sstableFiles, func(i, j int) bool {
		return sstableFiles[i] > sstableFiles[j]
	})
	return sstableFiles, nil
}
