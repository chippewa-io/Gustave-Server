#!/usr/bin/env swift
import Foundation

func shell(_ command: String) -> String {
    let task = Process()
    task.launchPath = "/bin/bash"
    task.arguments = ["-c", command]

    let pipe = Pipe()
    task.standardOutput = pipe
    task.launch()

    let data = pipe.fileHandleForReading.readDataToEndOfFile()
    let output = String(data: data, encoding: .utf8)!
    
    return output.trimmingCharacters(in: .whitespacesAndNewlines)
}

func concierge() {
    let regex = "^[a-fA-F0-9]{32}$"
    var secret = shell("defaults read /Library/Managed\\ Preferences/io.chippewa.gustave.plist Secret")
    
    if secret.range(of: regex, options: .regularExpression) != nil {
        print("Secret already exists.")
        return
    }

    let UDID = shell("system_profiler SPHardwareDataType | awk '/UUID/ { print $3;}'")
    let GustaveServer = "gustave.chippewa.io"

    var request = URLRequest(url: URL(string: "https://\(GustaveServer)/api/secret")!)
    request.httpMethod = "POST"
    let postString = "udid=\(UDID)"
    request.httpBody = postString.data(using: .utf8)
    let task = URLSession.shared.dataTask(with: request)
    task.resume()

    let max_attempts = 30
    var attempt = 0
    while true {
        secret = shell("defaults read /Library/Managed\\ Preferences/io.chippewa.gustave.plist Secret")
        if secret.range(of: regex, options: .regularExpression) != nil {
            print("Secret received.")
            break
        } else if attempt == max_attempts {
            print("Maximum attempts reached. Exiting.")
            return
        } else {
            attempt += 1
        }
        sleep(1)
    }
}

// Calling the function
concierge()
