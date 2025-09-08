/*
Copyright © 2025 NAME HERE <EMAIL ADDRESS>

*/
package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

// dbCmd represents the db command
var dbCmd = &cobra.Command{
	Use:   "db",
	Short: "Command to interface with our 'database'",
	Long: `
A golang implementation of the db_set and db_get
bash examples from DDIA Chapter 03.`,
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		// this runs before any subcommand
		dbPath, _ := cmd.Flags().GetString("db-path")
		fmt.Printf("Using database path: %s\n", dbPath)
	},
}

var dbSetCmd = &cobra.Command{
	Use: "set [key] [value]",
	Args: cobra.ExactArgs(2),
	Short: "Sets a key value pair in the 'database'",
	Run: func(cmd *cobra.Command, args []string) {
		dbPath, _ := cmd.Flags().GetString("db-path")
		err := dbSet(dbPath, args[0], args[1])
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			return 
		}
		fmt.Printf("Set %s=%s in %s\n", args[0], args[1], dbPath)
	},
}

var dbGetCmd = &cobra.Command{
	Use: "get [key]",
	Args: cobra.ExactArgs(1),
	Short: "Gets a value given a key from the 'database'",
	Run: func(cmd *cobra.Command, args []string) {
		dbPath, _ := cmd.Flags().GetString("db-path")
		value, err := dbGet(dbPath, args[0])
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			return
		}
		fmt.Printf("%s=%s in %s\n", args[0], value, dbPath)
	},

}

func init() {
	dbCmd.AddCommand(dbSetCmd)
	dbCmd.AddCommand(dbGetCmd)
	rootCmd.AddCommand(dbCmd)
	dbCmd.PersistentFlags().StringP("db-path", "P", "./database.txt", "Path to the database file.")

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// dbCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// dbCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}
