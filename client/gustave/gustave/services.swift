//
//  Services.swift
//  gustave
//
//  Created by Chris on 6/16/23.
//
import Foundation
import SQLite
import IOKit
import os.log

class Services {
    let db = Database()
    let gustaveServerURL = "https://gustave.chippewa.io" // Replace with your Gustave server URL
    let log = OSLog(subsystem: "io.chippewa.gustave", category: "Services")
    let spinner = Spinner()
    
    func generateSecret(spinner: Spinner, silent: Bool = false) {
        var secretGenerationCompleted = false
        DispatchQueue.global(qos: .background).async {
                while !secretGenerationCompleted {
                    if !silent {
                        // Update the spinner
                        spinner.tick()
                        usleep(200000) // sleep for 200 milliseconds
                    }
                }
                if !silent {
                    // Stop the spinner when done
                    spinner.stop()
                }
            }
            //print("getting secret...")
            os_log(.default, log: log, "getting secret...")
            
            if db.getUnexpiredSecret() != nil {
                //print("Using existing secret.")
                os_log(.default, log: log, "Using existing secret.")
                return
            }
            //print("No pre-existing secret found")
            os_log(.default, log: log, "No pre-existing secret found.")
            let udid = getUDID()
            let url = URL(string: "\(gustaveServerURL)/api/secret")!
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.httpBody = "udid=\(udid)".data(using: .utf8)

            let semaphore = DispatchSemaphore(value: 0)  // 1. Create a semaphore
            
        let task = URLSession.shared.dataTask(with: request) { [self] data, response, error in
                guard let data = data, error == nil else {
                    //print("Error: \(error?.localizedDescription ?? "Unknown error")")
                    os_log(.error, log: log, "Unknown error: %{public}@", error?.localizedDescription ?? "Unknown error")
                    return
                }
                
                if let _ = String(data: data, encoding: .utf8) {
                    let secret = self.getSecretFromPlist()
                    self.storeSecretInDatabase(secret: secret)
                    self.checkSecretStatus(secret: secret)
                    semaphore.signal()// 3. Signal the semaphore when the task is done
                } else {
                    //print("Failed to generate a secret.")
                    os_log(.error, log: log, "Failed to generate a secret: %{public}@", error?.localizedDescription ?? "No error description available")
                }
            }

            task.resume()

            semaphore.wait()  // 2. Wait for the semaphore to be signaled before returning from the function
        self.deleteProfileWithUDID(silent: silent, secretGenerationCompleted: &secretGenerationCompleted)
                }
    
    func updateComputer(id: String, value: String) {
        //print("Updating computer...")
        os_log(.default, log: log, "Updating computer...." )
        let udid = getUDID()
        let secretData = db.getMostRecentSecret()
        guard let secret = secretData?.secret else {
            //print("No secrets found in the database.")
            os_log(.default, log: log, "No secrets found in the database." )
            return
        }
        let url = URL(string: "\(gustaveServerURL)/api/computers/update")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        let json: [String: Any] = ["udid": udid, "secret": secret, "id": id, "value": value]
        let jsonData = try? JSONSerialization.data(withJSONObject: json)
        request.httpBody = jsonData
        let semaphore = DispatchSemaphore(value: 0) // 1. Create a semaphore
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            defer { semaphore.signal() } // 3. Signal the semaphore when the task is done
            guard let data = data, error == nil else {
                //print("Error: \(error?.localizedDescription ?? "Unknown error")")
                os_log(.error, log: self.log, "Error: %{public}@", error?.localizedDescription ?? "Unknown error")
                return
            }
            if let responseJSON = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] {
                print(responseJSON)
                os_log(.default, log: self.log, "Response from Jamf Pro: %{public}@", responseJSON.description)
            }
        }
        task.resume()
        semaphore.wait() // 2. Wait for the semaphore to be signaled before returning from the function
    }


    func getUDID() -> String {
        let platformExpert: io_service_t = IOServiceGetMatchingService(kIOMainPortDefault, IOServiceMatching("IOPlatformExpertDevice"))

        if platformExpert != IO_OBJECT_NULL {
            let uuidAsCFString = IORegistryEntryCreateCFProperty(platformExpert, kIOPlatformUUIDKey as CFString, kCFAllocatorDefault, 0).takeRetainedValue() as! CFString
            IOObjectRelease(platformExpert)
            os_log(.default, log: self.log, "UDID= %{public}@", uuidAsCFString as String)
            return uuidAsCFString as String
        }
        return ""
    }
    
    func deleteProfileWithUDID(silent: Bool = false, secretGenerationCompleted: inout Bool) {
            let UDID = getUDID()
            guard !UDID.isEmpty else {
                //print("Can't get UDID.  Is this a Virtual Machine?")
                os_log(.default, log: log, "Can't get UDID.  Is this a Virtual Machine?  Gustave does not support virtual machines without proper and unique UDIDs." )
                return
            }
            let semaphore = DispatchSemaphore(value: 0)
            let urlString = "\(gustaveServerURL)/api/profiles?udid=\(UDID)"
            guard let url = URL(string: urlString) else {
                //print("Invalid URL.")
                os_log(.default, log: log, "Invalid Gustave URL.  Check to see if the Gustave Configuration Profile has been installed" )
                return
            }

            var request = URLRequest(url: url)
            request.httpMethod = "DELETE"
            
            let task = URLSession.shared.dataTask(with: request) { data, response, error in
                if let error = error {
                    //print("Error: \(error)")
                    os_log(.error, log: self.log, "Error: %{public}@", error.localizedDescription)
                } else if let httpResponse = response as? HTTPURLResponse {
                    if !silent {
                                // Stop the spinner when done
                        self.spinner.stop()
                        var secretGenerationCompleted = true
                                
                            }
                    //print("Response status code: \(httpResponse.statusCode)")
                    os_log(.default, log: self.log, "Response status code: %d", httpResponse.statusCode)
                }
                semaphore.signal()
            }
            
            task.resume()
            semaphore.wait()
        
        }

    func storeSecretInDatabase(secret: String) {
        let expiration = getExpirationDate()
        db.insertSecret(secret: secret, expiration: expiration)
        //print("Secret stored.")
        os_log(.default, log: self.log, "Secret stored")
    }

    func getExpirationDate() -> String {
        let plistPath = "/Library/Managed Preferences/io.chippewa.gustave.plist"
        guard let plistData = FileManager.default.contents(atPath: plistPath) else {
            return ""
        }
        
        var format = PropertyListSerialization.PropertyListFormat.xml
        guard let plistDict = try? PropertyListSerialization.propertyList(from: plistData, options: .mutableContainersAndLeaves, format: &format) as? [String: Any],
              let secretDict = plistDict["Secret"] as? [String: Any],
              let expirationDate = secretDict["Expiration"] as? Int else {
            return ""
        }
        
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
                //print("Secret received.")
                storeSecretInDatabase(secret: secret)
                checkSecretStatus(secret: secret)
                break
            } else {
                // Regex match failed
                //print("...")
                attempts += 1
                if attempts < maxAttempts {
                    // Wait for 2 seconds before trying again
                    //print(".....")
                    let _ = semaphore.wait(timeout: .now() + .seconds(2))
                } else {
                    //print("Exiting after \(maxAttempts) attempts.")
                }
            }
        }

        return secret
    }



    func checkSecretStatus(secret: String) {
        let expirationDate = getExpirationDate()
        if expirationDate == "active" {
            //print("Secret is active.")
        } else {
            //print("Secret is not active or expired.")
        }
    }
    
    func queryComputer() {
        //print("Querying computer...")
        let udid = getUDID()
        let secretData = db.getMostRecentSecret()
        guard let secret = secretData?.secret else {
            //print("No secrets found in the database.")
            return
        }
        let url = URL(string: "\(gustaveServerURL)/api/computers")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        let json: [String: Any] = ["udid": udid, "secret": secret]
        let jsonData = try? JSONSerialization.data(withJSONObject: json)
        request.httpBody = jsonData

        let semaphore = DispatchSemaphore(value: 0)  // 1. Create a semaphore

        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            defer { semaphore.signal() }  // 3. Signal the semaphore when the task is done

            guard let data = data, error == nil else {
                //print("Error: \(error?.localizedDescription ?? "Unknown error")")
                return
            }
            if let responseJSON = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] {
                print(responseJSON)
            }
        }
        task.resume()

        semaphore.wait()  // 2. Wait for the semaphore to be signaled before returning from the function
    }


}
