//
//  DatabaseManager.swift
//  concierge
//
//  Created by Chris on 6/9/23.
//
import Foundation
import SQLite

class DatabaseManager {
    static let shared = DatabaseManager()
    let db: Connection

    private init() {
        let fileManager = FileManager.default
        let urls = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask)
        guard let appSupportURL = urls.first else {
            fatalError("Unable to find Application Support directory")
        }

        let appName = Bundle.main.infoDictionary?["CFBundleName"] as? String ?? "gustave"
        let appDirectory = appSupportURL.appendingPathComponent(appName, isDirectory: true)

        do {
            try fileManager.createDirectory(at: appDirectory, withIntermediateDirectories: true, attributes: nil)
        } catch {
            print("Unable to create directory: \(error)")
        }

        let dbURL = appDirectory.appendingPathComponent("db.sqlite3")
        do {
            db = try Connection(dbURL.path)
        } catch {
            fatalError("Unable to setup the database: \(error)")
        }
    }
}
