// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "AIFrameworkApp",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(
            name: "AIFrameworkApp",
            targets: ["AIFrameworkApp"]
        )
    ],
    dependencies: [
        // Add any external dependencies here if needed
    ],
    targets: [
        .executableTarget(
            name: "AIFrameworkApp",
            dependencies: []
        )
    ]
)
