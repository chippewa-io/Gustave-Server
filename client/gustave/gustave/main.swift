//
//  main.swift
//  gustave
//
//  Created by Chris on 6/16/23.
//
import Foundation

class Gustave {
    let db = Database()
    let services = Services()  // Create an instance of the Services class

    func initiate() {
        // This is where we will implement the logic to gather a secret.
        print("Initiating the process to gather a secret...")
        services.generateSecret()  // Call the generateSecret() function in the Services class
    }

    func read() {
        // This is where we will implement the logic to read a secret from the database.
        print("Reading the secret from the database...")
    }
}

var gustave = Gustave()

// Check for sudo
if getuid() != 0 {
    print("There was an error.\n\nThis application must be run as root. Try the sudo command.")
    exit(1)
}

// Print help docs
if CommandLine.arguments.contains("--help") || CommandLine.arguments.contains("-h") || CommandLine.arguments.contains("help") {
    help()
    exit(0)
}

// Rest of commands
if CommandLine.arguments.count > 1 {
    let command = CommandLine.arguments[1]

    switch command {
    case "initiate":
        gustave.initiate()
    case "read":
        gustave.read()
    default:
        print("Unknown command: \(command)")
    }
} else {
    print("No command entered.")
}
