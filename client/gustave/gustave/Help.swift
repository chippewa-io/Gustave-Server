//
// Help.swift
// gustave
//
// Created by Chris on 6/16/23.
//
// CommandLineInterface.swift
import Foundation

func help() {
 let helpText = """
 Usage: gustave [options]
 Options:
 -h, --help Show this help message and exit
 initiate Start the process of generating and storing a new secret
 read Read the stored secret from the database
 """
 print(helpText)
}
