//
// Database.swift
// gustave
//
// Created by Chris on 6/16/23.
//
import Foundation
import SQLite

class Database {
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
            print("Cannot connect to database: \(error)")
        }
    }
    
    func createTable() throws {
        do {
            try db?.run(secrets.create(ifNotExists: true) { t in
                t.column(id, primaryKey: .autoincrement)
                t.column(secret)
                t.column(expiration)
            })
        } catch {
            print("Cannot create table: \(error)")
        }
    }

    func insertSecret(secret: String, expiration: String) {
        let insert = secrets.insert(self.secret <- secret, self.expiration <- expiration)
        do {
            try db?.run(insert)
        } catch {
            print("Cannot insert secret: \(error)")
        }
    }
}
