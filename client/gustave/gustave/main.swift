//
//  main.swift
//  gustave
//
//  Created by Chris on 6/16/23.
//
import Foundation

// Check for sudo
if getuid() != 0 {
    print("There was an error.\n\nThis application must be run as root. Try the sudo command.")
    exit(1)
}

class Gustave {
    let db = Database()
    let services = Services()  // Create an instance of the Services class

    func initiate() {
        // This is where we will implement the logic to gather a secret.
        services.generateSecret()  // Call the generateSecret() function in the Services class
    }

    func read() {
        print("Reading the most recent secret from the database...")
        if let secretData = db.getMostRecentSecret() {
            let json = """
            {
                "secret": "\(secretData.secret)",
                "expiration": "\(secretData.expiration)"
            }
            """
            print(json)
        } else {
            print("No secrets found in the database.")
        }
    }
}

var gustave = Gustave()

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
    case "update":
        if CommandLine.arguments.count > 3 {
            let id = CommandLine.arguments[3]
            let value = CommandLine.arguments[4]
            gustave.services.updateComputer(id: id, value: value)
        } else {
            print("No ID or value entered.")
        }
    case "query":
        if CommandLine.arguments.count > 2 {
            let queryType = CommandLine.arguments[2]
            switch queryType {
            case "ea":
                gustave.services.queryComputer()
            default:
                print("Unknown query type: \(queryType)")
            }
        } else {
            print("No query type entered.")
        }

    default:
        print("Unknown command: \(command)")
    }
} else {
    print("No command entered.")
}
