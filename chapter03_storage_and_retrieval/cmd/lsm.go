package cmd
import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var globalLSM *LSMTree


var lsmCmd = &cobra.Command{
	Use: "lsm",
	Short: "Command to interface with the lsm database",
	Long: `
A golang implementation of an SSTable + LSMTree
to demonstrate how they can be faster.`,
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		sstablePrefix, _ := cmd.Flags().GetString("sstable-file-prefix")
		fmt.Printf("Using SSTable Prefix path: %s\n", sstablePrefix)
	},
}

var lsmDbSetCmd = &cobra.Command{
	Use: "set [key] value",
	Args: cobra.ExactArgs(2),
	Short: "Sets a key value pair in the database (LSM)",
	Long: `Sets a key value pair in the database file
	using SSTables and LSMTrees`,
	Run: func(cmd *cobra.Command, args []string) {
		sstablePrefix, _ := cmd.Flags().GetString("sstable-file-prefix")
		fmt.Printf("Called lsm set %s %s on %s.", args[0], args[1], sstablePrefix)
		err := globalLSM.Set(args[0], args[1], sstablePrefix)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			return
		}
		return
	},
}

var lsmDbGetCmd = &cobra.Command{
	Use: "get [key]",
	Args: cobra.ExactArgs(1),
	Short: "Gets a key from the database (LSM)",
	Long: `Gets a key from the database file,
	uses SSTables and LSMTrees.`,
	Run: func(cmd *cobra.Command, args []string) {
		sstablePrefix, _ := cmd.Flags().GetString("sstable-file-prefix")
		fmt.Printf("Called lsm get %s on %s.", args[0], sstablePrefix)
		value, err := globalLSM.Get(args[0], sstablePrefix)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			return
		}
		fmt.Printf("%s=%s", args[0], value)
		return
	},
}

func init() {
	globalLSM = NewLSMTree(1000) // Flush after 1000 entries
	lsmCmd.AddCommand(lsmDbSetCmd)
	lsmCmd.AddCommand(lsmDbGetCmd)
	rootCmd.AddCommand(lsmCmd)
	lsmCmd.PersistentFlags().StringP("sstable-file-prefix", "P", "./sstables/sstable", "Path to the SST+LSMT Database log directory")
}

