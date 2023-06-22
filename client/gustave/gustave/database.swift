//
// Database.swift
// gustave
//
// Created by Chris on 6/16/23.
//
import Foundation
import SQLite
import os.log

class Database {
    let log = OSLog(subsystem: "io.chippewa.gustave", category: "Database Operations")

    var db: Connection?
    let secrets = Table("secrets")
    let id = Expression<Int64>("id")
    let secret = Expression<String>("secret")
    let expiration = Expression<String>("expiration")
    
    init() {
        do {
            let fileManager = FileManager.default
            let dirPath = "/Library/Application Support/gustave"
            let dbPath = dirPath + "/database.db"
            
            // Create the directory if it doesn't exist
            if !fileManager.fileExists(atPath: dirPath) {
                try fileManager.createDirectory(atPath: dirPath, withIntermediateDirectories: true, attributes: nil)
            }
            
            db = try Connection(dbPath)
            try createTable()
        } catch {
            //print("Cannot connect to database: \(error)")
            os_log(.error, log: log, "Failed to connect to database: %{public}@", error.localizedDescription)

            
        }
    }
    
    func getUnexpiredSecret() -> (secret: String, expiration: String)? {
        if let mostRecentSecretData = getMostRecentSecret() {
            let currentTime = Int(Date().timeIntervalSince1970) // Get the current time in seconds
            if let expirationTime = Int(mostRecentSecretData.expiration), expirationTime > currentTime {
                // If the expiration time of the most recent secret is later than the current time, the secret is not expired
                //print("Using existing unexpired secret.")
                os_log(.default, log: log, "Using existing unexpired secret.")
                return mostRecentSecretData
            } else {
                //print("Most recent secret is expired.")
                os_log(.default, log: log, "Most recent secret is expired.")
            }
        } else {
            //print("No secret found in the database.")
            os_log(.default, log: log, "No secret found in the database.")
            
        }
        return nil
    }

    
    func createTable() throws {
        do {
            try db?.run(secrets.create(ifNotExists: true) { t in
                t.column(id, primaryKey: .autoincrement)
                t.column(secret)
                t.column(expiration)
            })
        } catch {
            //print("Cannot create table: \(error)")
            os_log(.error, log: log, "Cannot create table: %{public}@", error.localizedDescription)

        }
    }
    
    func getMostRecentSecret() -> (secret: String, expiration: String)? {
        do {
            if let row = try db?.pluck(secrets.order(id.desc)) {
                return (row[secret], row[expiration])
            }
        } catch {
            //print("Cannot retrieve secret: \(error)")
            os_log(.error, log: log, "Cannot retrieve secret: %{public}@", error.localizedDescription)
        }
        return nil
    }


    func insertSecret(secret: String, expiration: String) {
        let insert = secrets.insert(self.secret <- secret, self.expiration <- expiration)
        do {
            try db?.run(insert)
        } catch {
            //print("Cannot insert secret: \(error)")
            os_log(.error, log: log, "Cannot insert secret: %{public}@", error.localizedDescription)
        }
    }
}
