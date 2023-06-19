//
//  Services.swift
//  gustave
//
//  Created by Chris on 6/16/23.
//
import Foundation
import SQLite
import IOKit

class Services {
    let db = Database()
    let gustaveServerURL = "https://gustave.chippewa.io" // Replace with your Gustave server URL

    func generateSecret() {
        print("getting secret...")
        let udid = getUDID()
        let url = URL(string: "\(gustaveServerURL)/api/secret")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.httpBody = "udid=\(udid)".data(using: .utf8)

        let semaphore = DispatchSemaphore(value: 0)  // 1. Create a semaphore

        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            defer { semaphore.signal() }  // 3. Signal the semaphore when the task is done

            guard let data = data, error == nil else {
                print("Error: \(error?.localizedDescription ?? "Unknown error")")
                return
            }
            //print("data: \(data)")
            if let _ = String(data: data, encoding: .utf8) {
                let secret = self.getSecretFromPlist()
                self.storeSecretInDatabase(secret: secret)
                self.checkSecretStatus(secret: secret)
            } else {
                print("Failed to generate a secret.")
            }
        }

        task.resume()

        semaphore.wait()  // 2. Wait for the semaphore to be signaled before returning from the function
    }

    func getUDID() -> String {
        // This is a placeholder. Replace with your method to get the UDID.
        return "93A1E4DA-2838-53F7-A962-FEA4D4F2AC0E"
    }

    func storeSecretInDatabase(secret: String) {
        print("storeSecretInDatabase: Starting...")
        let expiration = getExpirationDate()
        print("storeSecretInDatabase: Got expiration date \(expiration)")
        db.insertSecret(secret: secret, expiration: expiration)
        print("storeSecretInDatabase: Secret stored.")
    }

    func getExpirationDate() -> String {
        print("getExpirationDate: Starting...")
        
        let plistPath = "/Library/Managed Preferences/io.chippewa.gustave.plist"
        guard let plistData = FileManager.default.contents(atPath: plistPath) else {
            print("getExpirationDate: Error reading plist file")
            return ""
        }
        
        var format = PropertyListSerialization.PropertyListFormat.xml
        guard let plistDict = try? PropertyListSerialization.propertyList(from: plistData, options: .mutableContainersAndLeaves, format: &format) as? [String: Any],
              let secretDict = plistDict["Secret"] as? [String: Any],
              let expirationDate = secretDict["Expiration"] as? Int else {
            print("getExpirationDate: Error reading plist file or finding 'Expiration' key")
            return ""
        }
        
        print("getExpirationDate: Got expiration date \(expirationDate)")
        return String(expirationDate)
    }

    
    func getSecretFromPlist(maxAttempts: Int = 5) -> String {
        let regexPattern = "^[a-fA-F0-9]{32}$"  // Replace with your actual regex pattern
        let defaults = UserDefaults(suiteName: "io.chippewa.gustave")

        var attempts = 0
        var secret = ""
        let semaphore = DispatchSemaphore(value: 0)

        let regex = try? NSRegularExpression(pattern: regexPattern)

        while attempts < maxAttempts {
            if let secretDict = defaults?.dictionary(forKey: "Secret"),
               let secretValue = secretDict["value"] as? String {
                secret = secretValue
            }
            
            if let _ = regex?.firstMatch(in: secret, options: [], range: NSRange(location: 0, length: secret.utf16.count)) {
                // Regex match succeeded
                print("Secret received.")
                storeSecretInDatabase(secret: secret)
                checkSecretStatus(secret: secret)
                break
            } else {
                // Regex match failed
                print("Failed to receive the secret.")
                attempts += 1
                if attempts < maxAttempts {
                    // Wait for 2 seconds before trying again
                    print("Retrying in 2 seconds...")
                    let _ = semaphore.wait(timeout: .now() + .seconds(2))
                } else {
                    print("Exiting after \(maxAttempts) attempts.")
                }
            }
        }

        return secret
    }



    func checkSecretStatus(secret: String) {
        print("checkSecretStatus: Starting...")
        let expirationDate = getExpirationDate()
        if expirationDate == "active" {
            print("checkSecretStatus: Secret is active.")
        } else {
            print("checkSecretStatus: Secret is not active or expired.")
        }
    }
}
