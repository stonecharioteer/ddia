/*
Copyright © 2025 NAME HERE <EMAIL ADDRESS>

*/
package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

// dbCmd represents the db command
var dbCmd = &cobra.Command{
	Use:   "db",
	Short: "Command to interface with our 'database'",
	Long: `A golang implementation of the db_set and db_get
	bash examples from DDIA Chapter 03`,
}

var dbSetCmd = &cobra.Command{
	Use: "set",
	Short: "Sets a key value pair in the 'database'",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("db set called")
	},
}

var dbGetCmd = &cobra.Command{
	Use: "get",
	Short: "Gets a value given a key from the 'database'",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("db set called")
	},

}

func init() {
	dbCmd.AddCommand(dbSetCmd)
	dbCmd.AddCommand(dbGetCmd)
	rootCmd.AddCommand(dbCmd)

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// dbCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// dbCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}
