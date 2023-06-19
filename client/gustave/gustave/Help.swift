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
 Usage: gustave verb [options]

     verb is one of the following:

     help             Displays this text and instructions on utilizing the gustave binary
     initiate         This will begin the process of requesting a secret from the gustave server.
     read             This will retrieve a secret from the database.  This secret can be utilized to query the gustave server.

 """
 print(helpText)
}
