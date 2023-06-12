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
    let mainCommand = arguments[1]
    
    switch mainCommand {
    case "get-token":
        gustaveService.getTokenFromGustave()
    case "check-token":
        gustaveService.checkForExistingToken()
    case "query-endpoint":
        gustaveService.queryGustaveEndpoint()
    case "retrieve":
        gustaveService.retrieve()
    case "gustave":
        if arguments.count > 2 {
            let subCommand = arguments[2]
            
            switch subCommand {
            case "chit":
                if arguments.count > 3 {
                    let chitAction = arguments[3]
                    switch chitAction {
                    case "create":
                        gustaveService.getTokenFromGustave()
                        // Add more cases for other chit actions if needed
                    default:
                        print("Invalid chit action")
                    }
                } else {
                    print("Missing chit action")
                }
            default:
                print("Invalid subcommand")
            }
        } else {
            print("Missing subcommand")
        }
    default:
        print("Invalid command")
    }
} else {
    print("Dude, you gotta give me some command to work with!")
}
