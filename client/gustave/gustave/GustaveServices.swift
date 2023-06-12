//
//  GustaveService.swift
//  concierge
//
//  Created by Chris on 6/9/23.
//

import Foundation
import IOKit
import SQLite
import os

//Logging Functionality
let log = OSLog(subsystem: "io.chippewa.gustave", category: "Concierge")


class GustaveService {
    static let shared = GustaveService()
    var gustaveServerURL: URL?
    var maxAttempts: Int?
    //Logging Functionality
    let log = OSLog(subsystem: "io.chippewa.gustave", category: "Concierge")

    
    func getSecretFromDatabase() -> String? {
        do {
            let query = tokens.select(token).limit(1)
            if let row = try db.pluck(query) {
                return row[token]
            } else {
                return nil
            }
        } catch {
            print("Rocket: Database retrieval failed: \(error)")
            return nil
        }
    }

    func retrieve() {
        // Make sure the Gustave server URL is configured
        guard let gustaveServerURL = gustaveServerURL else {
            print("Gustave server URL not configured.")
            return
        }

        // Get the UDID and secret
        let udid = getHardwareUUID()
        guard let secret = getSecretFromDatabase() else {
            print("Failed to retrieve secret.")
            return
        }

        // Prepare the URL
        let url = gustaveServerURL.appendingPathComponent("api/computers")

        // Prepare the request
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Prepare the JSON payload
        let payload = ["udid": udid, "secret": secret]
        request.httpBody = try? JSONSerialization.data(withJSONObject: payload)

        // Create a DispatchGroup to manage the task
        let group = DispatchGroup()
        group.enter()

        // Create the task
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error: \(error)")
            } else if let data = data {
                let str = String(data: data, encoding: .utf8)
                print("Received data:\n\(str ?? "")")
            }
            // Task completed, leave the group
            group.leave()
        }

        // Start the task
        task.resume()

        // Wait for the task to complete
        group.wait()
    }


    
    func getSecretFromPlist() -> String? {
        let plistPath = "/Library/Managed Preferences/io.chippewa.gustave.plist"
        let regex = try! NSRegularExpression(pattern: "^[a-fA-F0-9]{32}$", options: [])

        guard let plist = NSDictionary(contentsOfFile: plistPath),
              let secret = plist["Secret"] as? String,
              regex.firstMatch(in: secret, options: [], range: NSRange(location: 0, length: secret.utf16.count)) != nil else {
            return nil
        }
        return secret
    }
    
    func getTimeoutFromPlist() -> Int {
        let plistPath = "/Library/Managed Preferences/io.chippewa.gustave.plist"
        guard let plist = NSDictionary(contentsOfFile: plistPath),
              let timeout = plist["Timeout"] as? Int else {
            return 30 // Default value in case we can't get it from the plist
        }
        return timeout
    }


    func getTokenFromGustave() {
        let regex = try! NSRegularExpression(pattern: "^[a-fA-F0-9]{32}$", options: [])
        let maxAttempts = getTimeoutFromPlist()

        guard let gustaveServerURL = gustaveServerURL else {
            print("Gustave server URL not configured.")
            return
        }

        let url = gustaveServerURL.appendingPathComponent("api/secret")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        request.httpBody = "udid=\(getHardwareUUID())".data(using: .utf8)

        let task = URLSession.shared.dataTask(with: request)
        task.resume()

        var attempt = 0
        while true {
            if let secret = getSecretFromPlist(),
               regex.firstMatch(in: secret, options: [], range: NSRange(location: 0, length: secret.utf16.count)) != nil {
                print("Secret received.")
                storeToken(secret)
                break
            } else if attempt == maxAttempts {
                print("Maximum attempts reached. Exiting.")
                exit(1)
            } else {
                attempt += 1
            }
            sleep(1)
        }
    }


    func checkForExistingToken() {
        print("hello checkForExistingToken")
    }
    
    let token = Expression<String>("token")

    func storeToken(_ secret: String) {
            do {
                let insert = tokens.insert(token <- secret)
                try db.run(insert)
                os_log("Secret stored in the database.", log: log, type: .info)
                print("Secret stored in the database.")
            } catch {
                os_log("Error storing secret in the database: %{public}s", log: log, type: .error, error.localizedDescription)
                print("Error storing secret in the database: \(error)")
            }
        }

    func queryGustaveEndpoint() {
        // Use URLSession to make a request to your Flask app
    }

    func getHardwareUUID() -> String {
        let service: io_service_t = IOServiceGetMatchingService(kIOMainPortDefault, IOServiceMatching("IOPlatformExpertDevice"))
        let cfSerialNumber: CFTypeRef = IORegistryEntryCreateCFProperty(service, "IOPlatformUUID" as CFString, kCFAllocatorDefault, 0).takeRetainedValue()
        IOObjectRelease(service)
        return cfSerialNumber as! String
    }
}

struct Configuration {
    let gustaveServerURL: URL?
    let maxAttempts: Int?
}

extension GustaveService {
    func configure() {
        let defaults = UserDefaults(suiteName: "io.chippewa.gustave")
        let serverURLString = defaults?.string(forKey: "GustaveServerURL")
        
        guard let urlString = serverURLString, let url = URL(string: "https://" + urlString) else {
            os_log("Server URL not found in configuration profile.", log: log, type: .error)
            print("Server URL not found in configuration profile.")
            return
        }
        
        gustaveServerURL = url
    }
}
