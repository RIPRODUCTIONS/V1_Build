#!/usr/bin/env swift
// Simple AI Framework Desktop App for M3 Max
// This app integrates with your running AI Framework on port 8100

import SwiftUI
import Foundation

// MARK: - AI Framework Service Status
struct ServiceStatus: Identifiable {
    let id = UUID()
    let name: String
    let port: String
    let url: String
    var isHealthy: Bool = false
}

// MARK: - Main App
@main
struct SimpleAIFrameworkApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .windowStyle(.hiddenTitleBar)
        .windowToolbarStyle(.unified)
    }
}

// MARK: - Content View
struct ContentView: View {
    @State private var services: [ServiceStatus] = [
        ServiceStatus(name: "AI Framework", port: "8100", url: "http://localhost:8100/health"),
        ServiceStatus(name: "Grafana", port: "3002", url: "http://localhost:3002"),
        ServiceStatus(name: "Prometheus", port: "9092", url: "http://localhost:9092"),
        ServiceStatus(name: "PostgreSQL", port: "5434", url: "http://localhost:5434"),
        ServiceStatus(name: "Redis", port: "6380", url: "http://localhost:6380")
    ]
    
    @State private var isRefreshing = false
    @State private var lastRefreshTime = Date()
    
    var body: some View {
        VStack(spacing: 20) {
            // Header
            HStack {
                Image(systemName: "cpu.fill")
                    .foregroundColor(.blue)
                    .font(.title2)
                
                Text("AI Framework - M3 Max Dashboard")
                    .font(.title)
                    .fontWeight(.bold)
                
                Spacer()
                
                Button(action: refreshServices) {
                    Image(systemName: "arrow.clockwise")
                        .rotationEffect(.degrees(isRefreshing ? 360 : 0))
                        .animation(.linear(duration: 1).repeatForever(autoreverses: false), value: isRefreshing)
                }
                .buttonStyle(.bordered)
                .disabled(isRefreshing)
            }
            .padding()
            
            // M3 Max Hardware Info
            GroupBox("M3 Max Hardware") {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("CPU Cores:")
                        Spacer()
                        Text("12 (8 Performance + 4 Efficiency)")
                            .fontWeight(.semibold)
                    }
                    
                    HStack {
                        Text("GPU Cores:")
                        Spacer()
                        Text("40")
                            .fontWeight(.semibold)
                    }
                    
                    HStack {
                        Text("Neural Engine:")
                        Spacer()
                        Text("16 cores")
                            .fontWeight(.semibold)
                    }
                    
                    HStack {
                        Text("Unified Memory:")
                        Spacer()
                        Text("48GB")
                            .fontWeight(.semibold)
                    }
                }
            }
            .padding()
            
            // Service Status
            GroupBox("Service Status") {
                VStack(alignment: .leading, spacing: 8) {
                    ForEach($services) { $service in
                        ServiceRowView(service: $service)
                    }
                }
            }
            .padding()
            
            // Quick Actions
            HStack(spacing: 20) {
                Button("Open AI Framework") {
                    openURL("http://localhost:8100")
                }
                .buttonStyle(.borderedProminent)
                
                Button("Open Grafana") {
                    openURL("http://localhost:3002")
                }
                .buttonStyle(.bordered)
                
                Button("Open Prometheus") {
                    openURL("http://localhost:9092")
                }
                .buttonStyle(.bordered)
            }
            
            // Status Footer
            HStack {
                Text("Last updated: \(lastRefreshTime, style: .time)")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text("M3 Max Optimized")
                    .font(.caption)
                    .foregroundColor(.blue)
            }
            .padding(.horizontal)
            
            Spacer()
        }
        .frame(minWidth: 600, minHeight: 500)
        .onAppear {
            refreshServices()
        }
    }
    
    private func refreshServices() {
        isRefreshing = true
        
        // Check each service
        for i in services.indices {
            checkServiceHealth(for: i)
        }
        
        lastRefreshTime = Date()
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            isRefreshing = false
        }
    }
    
    private func checkServiceHealth(for index: Int) {
        let service = services[index]
        
        // Create URL request
        guard let url = URL(string: service.url) else { return }
        
        let task = URLSession.shared.dataTask(with: url) { data, response, error in
            DispatchQueue.main.async {
                if let httpResponse = response as? HTTPURLResponse,
                   httpResponse.statusCode == 200 {
                    services[index].isHealthy = true
                } else {
                    services[index].isHealthy = false
                }
            }
        }
        
        task.resume()
    }
    
    private func openURL(_ urlString: String) {
        guard let url = URL(string: urlString) else { return }
        NSWorkspace.shared.open(url)
    }
}

// MARK: - Service Row View
struct ServiceRowView: View {
    @Binding var service: ServiceStatus
    
    var body: some View {
        HStack {
            Circle()
                .fill(service.isHealthy ? Color.green : Color.red)
                .frame(width: 8, height: 8)
            
            Text(service.name)
                .fontWeight(.medium)
            
            Spacer()
            
            Text(":\(service.port)")
                .font(.caption)
                .foregroundColor(.secondary)
            
            Text(service.isHealthy ? "Healthy" : "Not Responding")
                .font(.caption)
                .foregroundColor(service.isHealthy ? .green : .red)
        }
    }
}
