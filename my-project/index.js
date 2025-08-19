import { Octokit } from '@octokit/rest';
import { createClient } from '@supabase/supabase-js';

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GITHUB_OWNER = process.env.GITHUB_OWNER;
const GITHUB_REPO = process.env.GITHUB_REPO;
const GITHUB_PATH = process.env.GITHUB_PATH || '';

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;

function createOctokitClient() {
  if (!GITHUB_TOKEN) return null;
  return new Octokit({ auth: GITHUB_TOKEN });
}

function createSupabaseClient() {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) return null;
  return createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
}

async function tryListRepoPath(octokit) {
  if (!octokit) return { skipped: true, reason: 'No GitHub token provided' };
  if (!GITHUB_OWNER || !GITHUB_REPO || !GITHUB_PATH) {
    return { skipped: true, reason: 'Missing GITHUB_OWNER, GITHUB_REPO, or GITHUB_PATH' };
  }
  const response = await octokit.repos.getContent({
    owner: GITHUB_OWNER,
    repo: GITHUB_REPO,
    path: GITHUB_PATH,
  });
  return { skipped: false, data: response.data };
}

async function tryQuerySupabase(supabase) {
  if (!supabase) return { skipped: true, reason: 'No Supabase credentials provided' };
  // Perform a lightweight, safe call: fetch current time from Postgres if a helper RPC exists; otherwise just return a connectivity check
  // Since we do not know the schema, we avoid querying a specific table.
  try {
    // Ping using auth getSession as a harmless call
    const { data, error } = await supabase.auth.getSession();
    if (error) throw error;
    return { skipped: false, data: { sessionPresent: Boolean(data?.session) } };
  } catch (error) {
    // If auth is not configured, just indicate client creation worked
    return { skipped: false, data: { clientCreated: true } };
  }
}

async function main() {
  try {
    const octokit = createOctokitClient();
    const supabase = createSupabaseClient();

    const [githubResult, supabaseResult] = await Promise.all([
      tryListRepoPath(octokit).catch((error) => ({ skipped: false, error })),
      tryQuerySupabase(supabase).catch((error) => ({ skipped: false, error })),
    ]);

    if (githubResult.error) {
      console.error('GitHub error:', githubResult.error);
    } else if (githubResult.skipped) {
      console.log('GitHub skipped:', githubResult.reason);
    } else {
      console.log('GitHub data:', githubResult.data);
    }

    if (supabaseResult.error) {
      console.error('Supabase error:', supabaseResult.error);
    } else if (supabaseResult.skipped) {
      console.log('Supabase skipped:', supabaseResult.reason);
    } else {
      console.log('Supabase data:', supabaseResult.data);
    }
  } catch (error) {
    console.error('Unexpected error in main():', error);
    process.exitCode = 1;
  }
}

main();