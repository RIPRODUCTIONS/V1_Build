// GitHub and Supabase Integration Example
const { Octokit } = require('@octokit/rest');
const { createClient } = require('@supabase/supabase-js');

// Configuration from environment variables
const GITHUB_TOKEN = process.env.GITHUB_ACCESS_TOKEN;
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_ANON_KEY;

// Initialize clients
let octokit, supabase;

function initializeClients() {
    if (GITHUB_TOKEN) {
        octokit = new Octokit({
            auth: GITHUB_TOKEN,
        });
        console.log('✅ GitHub client initialized');
    } else {
        console.warn('⚠️  GitHub token not provided. GitHub functionality will be limited.');
    }

    if (SUPABASE_URL && SUPABASE_KEY) {
        supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
        console.log('✅ Supabase client initialized');
    } else {
        console.warn('⚠️  Supabase credentials not provided. Database functionality will be unavailable.');
    }
}

// GitHub Functions
async function getRepositoryInfo(owner, repo) {
    if (!octokit) {
        throw new Error('GitHub client not initialized. Please provide GITHUB_ACCESS_TOKEN.');
    }
    
    try {
        const { data } = await octokit.repos.get({
            owner,
            repo,
        });
        
        return {
            name: data.name,
            description: data.description,
            stars: data.stargazers_count,
            forks: data.forks_count,
            issues: data.open_issues_count,
            language: data.language,
            updated: data.updated_at
        };
    } catch (error) {
        console.error('Error fetching repository info:', error.message);
        throw error;
    }
}

async function getOpenIssues(owner, repo, limit = 10) {
    if (!octokit) {
        throw new Error('GitHub client not initialized. Please provide GITHUB_ACCESS_TOKEN.');
    }
    
    try {
        const { data } = await octokit.issues.listForRepo({
            owner,
            repo,
            state: 'open',
            per_page: limit,
            sort: 'created',
            direction: 'desc'
        });
        
        return data.map(issue => ({
            number: issue.number,
            title: issue.title,
            state: issue.state,
            created_at: issue.created_at,
            user: issue.user.login,
            labels: issue.labels.map(label => label.name),
            url: issue.html_url
        }));
    } catch (error) {
        console.error('Error fetching issues:', error.message);
        throw error;
    }
}

// Supabase Functions
async function storeRepositoryData(repoData) {
    if (!supabase) {
        console.warn('Supabase not initialized. Skipping database storage.');
        return null;
    }
    
    try {
        const { data, error } = await supabase
            .from('repositories')
            .upsert([{
                name: repoData.name,
                description: repoData.description,
                stars: repoData.stars,
                forks: repoData.forks,
                issues: repoData.issues,
                language: repoData.language,
                updated_at: repoData.updated,
                last_synced: new Date().toISOString()
            }]);
        
        if (error) throw error;
        return data;
    } catch (error) {
        console.error('Error storing repository data:', error.message);
        throw error;
    }
}

async function storeIssuesData(issues, repoName) {
    if (!supabase) {
        console.warn('Supabase not initialized. Skipping database storage.');
        return null;
    }
    
    try {
        const issuesData = issues.map(issue => ({
            issue_number: issue.number,
            title: issue.title,
            state: issue.state,
            created_at: issue.created_at,
            user_login: issue.user,
            labels: issue.labels,
            url: issue.url,
            repository: repoName,
            last_synced: new Date().toISOString()
        }));
        
        const { data, error } = await supabase
            .from('issues')
            .upsert(issuesData);
        
        if (error) throw error;
        return data;
    } catch (error) {
        console.error('Error storing issues data:', error.message);
        throw error;
    }
}

// Main execution function
async function main() {
    console.log('🚀 Starting GitHub and Supabase integration...');
    
    // Initialize clients
    initializeClients();
    
    // Default repository for testing (can be overridden by command line args)
    const owner = process.argv[2] || process.env.GITHUB_OWNER || 'RIPRODUCTIONS';
    const repo = process.argv[3] || process.env.GITHUB_REPO || 'V1_Build';
    
    try {
        // Fetch repository information
        console.log(`📊 Fetching repository info for ${owner}/${repo}...`);
        const repoData = await getRepositoryInfo(owner, repo);
        console.log('Repository Info:', repoData);
        
        // Store repository data
        await storeRepositoryData(repoData);
        
        // Fetch open issues
        console.log('🐛 Fetching open issues...');
        const issues = await getOpenIssues(owner, repo);
        console.log(`Found ${issues.length} open issues`);
        
        // Store issues data
        await storeIssuesData(issues, repo);
        
        // Summary
        console.log('\n📋 Summary:');
        console.log(`- Repository: ${repoData.name}`);
        console.log(`- Stars: ${repoData.stars}`);
        console.log(`- Open Issues: ${repoData.issues}`);
        console.log(`- Primary Language: ${repoData.language}`);
        console.log(`- Last Updated: ${repoData.updated}`);
        
        console.log('\n✅ Integration completed successfully!');
        
    } catch (error) {
        console.error('❌ Error during execution:', error.message);
        process.exit(1);
    }
}

// Export functions for use in other modules
module.exports = {
    initializeClients,
    getRepositoryInfo,
    getOpenIssues,
    storeRepositoryData,
    storeIssuesData,
    main
};

// Run main function if this file is executed directly
if (require.main === module) {
    main();
}