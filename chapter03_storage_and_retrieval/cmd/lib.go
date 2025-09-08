package cmd
import (
	"fmt"
	"os"
	"strings"
	"bufio"
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
