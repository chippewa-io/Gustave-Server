//
//  main.swift
//  concierge
//
//  Created by Chris on 6/9/23.
//
// main.swift

import Foundation
import SQLite

// Define your tables here

let tokens = Table("tokens")
let id = Expression<Int64>("id")
let token = Expression<String>("token")

// Get the shared database connection
let db = DatabaseManager.shared.db

// Check if the table exists
let tableName = "tokens"
let tableExistsQuery = "SELECT name FROM sqlite_master WHERE type='table' AND name='\(tableName)'"
let tableExists = try db.scalar(tableExistsQuery) as? String != nil



if !tableExists {
    // Table does not exist, create it
    try db.run(tokens.create { t in
        t.column(id, primaryKey: true)
        t.column(token)
    })
}

// Create an instance of GustaveService
let gustaveService = GustaveService.shared
gustaveService.configure()

// Parse command line arguments and call the appropriate function
let arguments = CommandLine.arguments

if arguments.count > 1 {
    switch arguments[1] {
    case "get-token":
        gustaveService.getTokenFromGustave()
    case "check-token":
        gustaveService.checkForExistingToken()
    case "query-endpoint":
        gustaveService.queryGustaveEndpoint()
    case "retrieve":
        gustaveService.retrieve()
    default:
        print("Invalid command")
    }
} else {
    print("Dude, you gotta give me some command to work with!")
}
 
