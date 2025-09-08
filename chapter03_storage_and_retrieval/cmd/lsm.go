package cmd
import (
	"fmt"

	"github.com/spf13/cobra"
)

var lsmCmd = &cobra.Command{
	Use: "lsm",
	Short: "Command to interface with the lsm database",
	Long: `
A golang implementation of an SSTable + LSMTree
to demonstrate how they can be faster.`,
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		dbPath, _ := cmd.Flags().GetString("db-path")
		fmt.Printf("Using database path: %s\n", dbPath)
	},
}

var lsmDbSetCmd = &cobra.Command{
	Use: "set [key] value",
	Args: cobra.ExactArgs(2),
	Short: "Sets a key value pair in the database (LSM)",
	Long: `Sets a key value pair in the database file
	using SSTables and LSMTrees`,
	Run: func(cmd *cobra.Command, args []string) {
		dbPath, _ := cmd.Flags().GetString("db-path")
		fmt.Printf("Called lsm set %s %s on %s.", args[0], args[1], dbPath)
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
		dbPath, _ := cmd.Flags().GetString("db-path")
		fmt.Printf("Called lsm get %s on %s.", args[0], dbPath)
		return
	},
}

func init() {
	lsmCmd.AddCommand(lsmDbSetCmd)
	lsmCmd.AddCommand(lsmDbGetCmd)
	rootCmd.AddCommand(lsmCmd)
	lsmCmd.PersistentFlags().StringP("db-path", "P", "./database-lsm.log", "Path to the SST+LSMT Database log")
}

