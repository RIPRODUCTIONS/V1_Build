const { GitHubUtils, SupabaseUtils, RateLimiter, handleError, validateEnvironment } = require('./index');

// Mock environment variables for testing
process.env.GITHUB_TOKEN = 'test-token';
process.env.SUPABASE_URL = 'https://test.supabase.co';
process.env.SUPABASE_ANON_KEY = 'test-key';

describe('n8n Automation Utilities', () => {
  describe('validateEnvironment', () => {
    it('should pass when all required environment variables are set', () => {
      expect(() => validateEnvironment()).not.toThrow();
    });

    it('should throw when required environment variables are missing', () => {
      const originalToken = process.env.GITHUB_TOKEN;
      delete process.env.GITHUB_TOKEN;
      
      expect(() => validateEnvironment()).toThrow();
      
      process.env.GITHUB_TOKEN = originalToken;
    });
  });

  describe('RateLimiter', () => {
    let rateLimiter;

    beforeEach(() => {
      rateLimiter = new RateLimiter(2, 1000); // 2 requests per second
    });

    it('should allow requests within limit', async () => {
      await expect(rateLimiter.checkLimit('user1')).resolves.toBe(true);
      await expect(rateLimiter.checkLimit('user1')).resolves.toBe(true);
    });

    it('should reject requests over limit', async () => {
      await rateLimiter.checkLimit('user2');
      await rateLimiter.checkLimit('user2');
      
      await expect(rateLimiter.checkLimit('user2')).rejects.toThrow('Rate limit exceeded');
    });

    it('should reset limits after time window', (done) => {
      rateLimiter.checkLimit('user3')
        .then(() => rateLimiter.checkLimit('user3'))
        .then(() => {
          setTimeout(async () => {
            await expect(rateLimiter.checkLimit('user3')).resolves.toBe(true);
            done();
          }, 1100);
        });
    });
  });

  describe('GitHubUtils', () => {
    let githubUtils;

    beforeEach(() => {
      githubUtils = new GitHubUtils();
    });

    it('should initialize with token', () => {
      expect(githubUtils.octokit).toBeDefined();
    });

    it('should throw error without token', () => {
      const originalToken = process.env.GITHUB_TOKEN;
      delete process.env.GITHUB_TOKEN;
      
      expect(() => new GitHubUtils()).toThrow('GITHUB_TOKEN environment variable is required');
      
      process.env.GITHUB_TOKEN = originalToken;
    });
  });

  describe('SupabaseUtils', () => {
    let supabaseUtils;

    beforeEach(() => {
      supabaseUtils = new SupabaseUtils();
    });

    it('should initialize with URL and key', () => {
      expect(supabaseUtils.supabase).toBeDefined();
    });

    it('should throw error without credentials', () => {
      const originalUrl = process.env.SUPABASE_URL;
      delete process.env.SUPABASE_URL;
      
      expect(() => new SupabaseUtils()).toThrow('Supabase environment variables are required');
      
      process.env.SUPABASE_URL = originalUrl;
    });
  });

  describe('handleError', () => {
    let consoleSpy;

    beforeEach(() => {
      consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    });

    afterEach(() => {
      consoleSpy.mockRestore();
    });

    it('should log error message', () => {
      const error = new Error('Test error');
      handleError(error, 'test context');
      
      expect(consoleSpy).toHaveBeenCalledWith('Error test context:', 'Test error');
    });

    it('should log stack trace if available', () => {
      const error = new Error('Test error');
      handleError(error);
      
      expect(consoleSpy).toHaveBeenCalledWith('Stack trace:', error.stack);
    });
  });
});