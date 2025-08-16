// swift-tools-version: 5.9
// Package.swift
// Save as: M3MaxDashboard/Package.swift

import PackageDescription

let package = Package(
    name: "M3MaxDashboard",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(
            name: "M3MaxDashboard",
            targets: ["M3MaxDashboard"]
        ),
    ],
    targets: [
        .executableTarget(
            name: "M3MaxDashboard",
            dependencies: []
        ),
    ]
)
