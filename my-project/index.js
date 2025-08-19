#!/usr/bin/env node
/**
 * n8n Automation Utilities
 * Provides utility functions for n8n workflow automation
 */

const { Octokit } = require('@octokit/rest');
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

// Configuration validation
function validateEnvironment() {
  const required = ['GITHUB_TOKEN', 'SUPABASE_URL', 'SUPABASE_ANON_KEY'];
  const missing = required.filter(env => !process.env[env]);
  
  if (missing.length > 0) {
    console.error('Missing required environment variables:', missing.join(', '));
    console.error('Please check your .env file');
    process.exit(1);
  }
}

// GitHub utilities
class GitHubUtils {
  constructor() {
    if (!process.env.GITHUB_TOKEN) {
      throw new Error('GITHUB_TOKEN environment variable is required');
    }
    
    this.octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN,
    });
  }

  async getRepositoryIssues(owner, repo, options = {}) {
    try {
      const { data } = await this.octokit.rest.issues.listForRepo({
        owner,
        repo,
        state: options.state || 'open',
        per_page: options.limit || 30,
      });
      return data;
    } catch (error) {
      console.error('Error fetching repository issues:', error.message);
      throw error;
    }
  }

  async createIssue(owner, repo, title, body) {
    try {
      const { data } = await this.octokit.rest.issues.create({
        owner,
        repo,
        title,
        body,
      });
      return data;
    } catch (error) {
      console.error('Error creating issue:', error.message);
      throw error;
    }
  }
}

// Supabase utilities
class SupabaseUtils {
  constructor() {
    if (!process.env.SUPABASE_URL || !process.env.SUPABASE_ANON_KEY) {
      throw new Error('Supabase environment variables are required');
    }
    
    this.supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_ANON_KEY
    );
  }

  async insertData(table, data) {
    try {
      const { data: result, error } = await this.supabase
        .from(table)
        .insert(data);
      
      if (error) throw error;
      return result;
    } catch (error) {
      console.error('Error inserting data:', error.message);
      throw error;
    }
  }

  async queryData(table, filters = {}) {
    try {
      let query = this.supabase.from(table).select('*');
      
      Object.entries(filters).forEach(([key, value]) => {
        query = query.eq(key, value);
      });
      
      const { data, error } = await query;
      
      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error querying data:', error.message);
      throw error;
    }
  }
}

// Rate limiting utility
class RateLimiter {
  constructor(maxRequests = 10, windowMs = 60000) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
    this.requests = new Map();
  }

  async checkLimit(identifier) {
    const now = Date.now();
    const windowStart = now - this.windowMs;
    
    if (!this.requests.has(identifier)) {
      this.requests.set(identifier, []);
    }
    
    const userRequests = this.requests.get(identifier);
    
    // Remove old requests outside the window
    const validRequests = userRequests.filter(time => time > windowStart);
    this.requests.set(identifier, validRequests);
    
    if (validRequests.length >= this.maxRequests) {
      throw new Error(`Rate limit exceeded for ${identifier}`);
    }
    
    validRequests.push(now);
    return true;
  }
}

// Error handling utility
function handleError(error, context = '') {
  console.error(`Error ${context}:`, error.message);
  
  if (error.stack) {
    console.error('Stack trace:', error.stack);
  }
  
  // Log to external service in production
  if (process.env.NODE_ENV === 'production') {
    // TODO: Implement logging to external service
    console.log('Error logged to monitoring service');
  }
}

// Main application
async function main() {
  try {
    console.log('🚀 n8n Automation Utilities Starting...');
    
    // Validate environment
    validateEnvironment();
    
    // Initialize utilities
    const github = new GitHubUtils();
    const supabase = new SupabaseUtils();
    const rateLimiter = new RateLimiter();
    
    console.log('✅ All utilities initialized successfully');
    console.log('Ready to process n8n automation requests');
    
    // Example usage (remove in production)
    if (process.env.NODE_ENV === 'development') {
      console.log('\n📝 Example: Testing GitHub API connection...');
      try {
        await rateLimiter.checkLimit('github-test');
        // Replace with actual repo details for testing
        // const issues = await github.getRepositoryIssues('owner', 'repo');
        // console.log(`Found ${issues.length} issues`);
        console.log('GitHub API connection test skipped (no repo specified)');
      } catch (error) {
        handleError(error, 'GitHub API test');
      }
    }
    
  } catch (error) {
    handleError(error, 'Application startup');
    process.exit(1);
  }
}

// Export utilities for use in n8n workflows
module.exports = {
  GitHubUtils,
  SupabaseUtils,
  RateLimiter,
  handleError,
  validateEnvironment
};

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    handleError(error, 'Main execution');
    process.exit(1);
  });
}
