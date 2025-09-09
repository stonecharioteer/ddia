package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var globalLSM *LSMTree

var lsmCmd = &cobra.Command{
	Use:   "lsm",
	Short: "Command to interface with the lsm database",
	Long: `
A golang implementation of an SSTable + LSMTree
to demonstrate how they can be faster.`,
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		return
	},
}

var lsmDbSetCmd = &cobra.Command{
	Use:   "set [key] value",
	Args:  cobra.ExactArgs(2),
	Short: "Sets a key value pair in the database (LSM)",
	Long: `Sets a key value pair in the database file
	using SSTables and LSMTrees`,
	Run: func(cmd *cobra.Command, args []string) {
		host, _ := cmd.Flags().GetString("host")
		port, _ := cmd.Flags().GetString("port")
		serverURL := fmt.Sprintf("http://%s:%s", host, port)

		err := makeHTTPSetRequest(serverURL, args[0], args[1])
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			return
		}
		fmt.Printf("Set %s=%s\n", args[0], args[1])
	},
}

var lsmDbGetCmd = &cobra.Command{
	Use:   "get [key]",
	Args:  cobra.ExactArgs(1),
	Short: "Gets a key from the database (LSM)",
	Long: `Gets a key from the database file,
	uses SSTables and LSMTrees.`,
	Run: func(cmd *cobra.Command, args []string) {
		host, _ := cmd.Flags().GetString("host")
		port, _ := cmd.Flags().GetString("port")
		serverURL := fmt.Sprintf("http://%s:%s", host, port)
		value, err := makeHTTPGetRequest(serverURL, args[0])
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			return
		}
		fmt.Printf("%s=%s", args[0], value)
	},
}

var lsmServeCmd = &cobra.Command{
	Use:   "serve",
	Short: "Start the LSM-Tree HTTP Server",
	Long:  `Starts an HTTP Server with an in-memory LSM-Tree`,
	Run: func(cmd *cobra.Command, args []string) {
		port, _ := cmd.Flags().GetString("port")
		sstablePrefix, _ := cmd.Flags().GetString("sstable-prefix")
		maxMemTableSize, _ := cmd.Flags().GetInt("max-memtable-size")
		fmt.Printf("Starting LSMTree server on port %s...\n", port)
		startLSMServer(port, sstablePrefix, maxMemTableSize)
	},
}

func init() {
	lsmCmd.AddCommand(lsmDbSetCmd)
	lsmCmd.AddCommand(lsmDbGetCmd)
	lsmCmd.AddCommand(lsmServeCmd)
	rootCmd.AddCommand(lsmCmd)
	lsmServeCmd.PersistentFlags().StringP("sstable-prefix", "P", "sstable", "Path to the SST+LSMT Database log directory")
	lsmServeCmd.PersistentFlags().IntP("max-memtable-size", "m", 1000, "Maximum entries in the memtable before flush.")
	// client flags (for set/get commands)
	lsmCmd.PersistentFlags().StringP("host", "H", "localhost", "LSM server host")
	lsmCmd.PersistentFlags().StringP("port", "p", "8080", "LSM server port")
}
