# Security Guidelines for n8n Automation Workflows

## 🔒 Critical Security Issues Addressed

This document outlines security vulnerabilities found in the repository and the measures taken to address them.

## 🚨 Security Vulnerabilities Fixed

### 1. Hardcoded Credentials
**Issue:** Plain text credentials in `.env` file committed to version control  
**Risk:** HIGH - Exposed passwords, potential unauthorized access  
**Fix:** 
- Added `.env` to `.gitignore`
- Created `.env.example` template
- Updated documentation to use environment variables
- Added security warnings in setup script

### 2. API Key Management
**Issue:** Hardcoded API keys in workflow files  
**Risk:** MEDIUM - API key exposure, potential service abuse  
**Fix:**
- Updated workflows to use environment variables: `={{$env.API_KEY_NAME}}`
- Created secure workflow examples
- Added API key management guidelines

### 3. File Permissions
**Issue:** Overly permissive file permissions (644 for workflow files)  
**Risk:** MEDIUM - Sensitive configuration exposure  
**Fix:**
- Changed workflow file permissions to 640 (owner read/write, group read)
- Set directory permissions to 750
- Added .env file protection (600)

### 4. Input Injection Vulnerabilities
**Issue:** Direct interpolation of user input without sanitization  
**Risk:** HIGH - Email injection, potential data exposure  
**Fix:**
- Created secure workflow with input sanitization
- Added sanitization functions for email content
- Limited input length and removed dangerous characters

### 5. Insecure Network Configuration
**Issue:** Docker service exposed without proper security  
**Risk:** MEDIUM - Unauthorized access to n8n instance  
**Fix:**
- Added HTTPS/TLS configuration guidance
- Enhanced basic auth configuration
- Added secure cookie settings

## 🛡️ Security Best Practices

### Credential Management
1. **Never commit credentials to version control**
   - Use `.env.example` for templates
   - Keep `.env` in `.gitignore`
   - Use strong, unique passwords

2. **Environment Variables**
   ```bash
   # In .env file
   OPENWEATHER_API_KEY=your_secure_api_key
   GITHUB_TOKEN=your_github_token
   SLACK_WEBHOOK_URL=your_webhook_url
   ```

3. **In n8n workflows, reference environment variables:**
   ```json
   {
     "appid": "={{$env.OPENWEATHER_API_KEY}}"
   }
   ```

### Input Validation and Sanitization
1. **Always sanitize user input before processing:**
   ```javascript
   const sanitizeText = (text) => {
     if (!text) return '';
     return text.toString()
       .replace(/[<>\"'&]/g, '') // Remove dangerous chars
       .substring(0, 1000); // Limit length
   };
   ```

2. **Validate email addresses:**
   ```javascript
   const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
   ```

3. **Use environment variables for email addresses:**
   ```json
   {
     "toEmail": "={{$env.ADMIN_EMAIL || 'fallback@company.com'}}"
   }
   ```

### File Security
1. **Secure file permissions:**
   ```bash
   chmod 750 workflows/          # Directory: owner+group access
   chmod 640 workflows/*.json    # Files: owner rw, group r
   chmod 600 .env               # Credentials: owner only
   ```

2. **Protect sensitive directories:**
   - Exclude logs from version control
   - Secure n8n data directories
   - Use proper Docker volume permissions

### Network Security
1. **Enable HTTPS in production:**
   ```yaml
   # docker-compose.yml
   environment:
     - N8N_PROTOCOL=https
     - N8N_SSL_KEY=/path/to/key.pem
     - N8N_SSL_CERT=/path/to/cert.pem
   ```

2. **Secure authentication:**
   ```env
   N8N_BASIC_AUTH_ACTIVE=true
   N8N_BASIC_AUTH_USER=admin
   N8N_BASIC_AUTH_PASSWORD=strong_secure_password_here
   N8N_SECURE_COOKIE=true
   ```

3. **Network isolation:**
   - Use Docker networks for isolation
   - Restrict port exposure
   - Consider reverse proxy setup

## 🔍 Security Checklist

Before deploying workflows, ensure:

- [ ] All credentials moved to environment variables
- [ ] Strong passwords set for all services
- [ ] Input validation implemented for user data
- [ ] File permissions properly configured
- [ ] HTTPS enabled for production
- [ ] Security logging enabled
- [ ] Regular security updates scheduled
- [ ] Access logs monitored
- [ ] Backup and recovery procedures tested

## 📋 Workflow Security Standards

### For Email Workflows:
- [ ] Input sanitization implemented
- [ ] Email addresses validated
- [ ] Content length limited
- [ ] Dangerous characters filtered

### For API Workflows:
- [ ] API keys in environment variables
- [ ] Rate limiting implemented
- [ ] Error handling configured
- [ ] Response validation added

### For Database Workflows:
- [ ] SQL injection prevention
- [ ] Connection string security
- [ ] Access control configured
- [ ] Audit logging enabled

## 🚨 Incident Response

If security issues are discovered:

1. **Immediate Actions:**
   - Disable affected workflows
   - Rotate compromised credentials
   - Review access logs
   - Document the incident

2. **Assessment:**
   - Determine scope of impact
   - Identify affected systems
   - Check for data exposure
   - Assess business impact

3. **Remediation:**
   - Apply security fixes
   - Update configurations
   - Test security measures
   - Update documentation

4. **Prevention:**
   - Review security practices
   - Update training materials
   - Enhance monitoring
   - Schedule security audits

## 📞 Security Resources

- [n8n Security Best Practices](https://docs.n8n.io/hosting/security/)
- [Docker Security Guide](https://docs.docker.com/engine/security/)
- [Environment Variable Management](https://12factor.net/config)
- [OWASP Input Validation](https://owasp.org/www-project-cheat-sheets/cheatsheets/Input_Validation_Cheat_Sheet.html)

## 🔄 Regular Security Tasks

### Weekly:
- Review workflow execution logs
- Check for failed authentication attempts
- Monitor resource usage

### Monthly:
- Update dependencies and Docker images
- Review and rotate API keys
- Audit user access and permissions
- Test backup and recovery procedures

### Quarterly:
- Conduct security assessments
- Review and update security documentation
- Test incident response procedures
- Security training for team members

---

**Remember:** Security is an ongoing process, not a one-time setup. Regularly review and update these practices as your automation environment evolves.