#!/bin/bash

# Security Scanning Script
# Runs multiple security checks on the codebase

set -e

echo "🔒 Starting Security Scan..."
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Dependency Vulnerability Scan
echo ""
echo "📦 Scanning dependencies for vulnerabilities..."
npm audit --production || {
    echo -e "${RED}❌ Vulnerabilities found in dependencies${NC}"
    echo "Run 'npm audit fix' to fix automatically fixable issues"
}

# 2. Check for outdated packages
echo ""
echo "📅 Checking for outdated packages..."
npm outdated || echo -e "${YELLOW}⚠️  Some packages are outdated${NC}"

# 3. Check for secrets in code
echo ""
echo "🔑 Scanning for exposed secrets..."
if command -v gitleaks &> /dev/null; then
    gitleaks detect --source . --verbose || {
        echo -e "${RED}❌ Potential secrets found${NC}"
        exit 1
    }
else
    echo -e "${YELLOW}⚠️  Gitleaks not installed. Skipping secret scan.${NC}"
    echo "Install with: brew install gitleaks (macOS) or see https://github.com/gitleaks/gitleaks"
fi

# 4. Check for common security issues in code
echo ""
echo "🔍 Scanning for common security issues..."

# Check for console.log in production code
if grep -r "console\.log" app/ lib/ --include="*.ts" --include="*.tsx" | grep -v "console\.error" | grep -v "console\.warn"; then
    echo -e "${YELLOW}⚠️  console.log found in code (should be removed in production)${NC}"
fi

# Check for hardcoded secrets patterns
if grep -r -i "password\s*=\s*['\"]" app/ lib/ --include="*.ts" --include="*.tsx"; then
    echo -e "${RED}❌ Hardcoded password found${NC}"
    exit 1
fi

if grep -r "api[_-]?key\s*=\s*['\"]" app/ lib/ --include="*.ts" --include="*.tsx"; then
    echo -e "${RED}❌ Hardcoded API key found${NC}"
    exit 1
fi

# Check for eval() usage
if grep -r "eval(" app/ lib/ --include="*.ts" --include="*.tsx"; then
    echo -e "${RED}❌ eval() usage found (security risk)${NC}"
    exit 1
fi

# Check for dangerouslySetInnerHTML
if grep -r "dangerouslySetInnerHTML" app/ --include="*.tsx"; then
    echo -e "${YELLOW}⚠️  dangerouslySetInnerHTML found (XSS risk)${NC}"
fi

# 5. TypeScript type checking
echo ""
echo "📝 Running TypeScript type checking..."
npm run type-check || {
    echo -e "${RED}❌ TypeScript errors found${NC}"
    exit 1
}

# 6. Linting
echo ""
echo "🎨 Running ESLint..."
npm run lint || {
    echo -e "${RED}❌ Linting errors found${NC}"
    exit 1
}

# 7. Check for missing security headers
echo ""
echo "🛡️  Checking security configuration..."
if ! grep -q "Strict-Transport-Security" next.config.js; then
    echo -e "${RED}❌ HSTS header not configured${NC}"
    exit 1
fi

if ! grep -q "X-Frame-Options" next.config.js; then
    echo -e "${RED}❌ X-Frame-Options header not configured${NC}"
    exit 1
fi

# 8. Check for proper authentication guards
echo ""
echo "🔐 Checking authentication implementation..."
if ! grep -q "AuthGuard" app/\(dashboard\)/layout.tsx 2>/dev/null; then
    echo -e "${YELLOW}⚠️  AuthGuard might not be implemented in dashboard${NC}"
fi

# 9. Verify HTTPS enforcement
echo ""
echo "🔒 Checking HTTPS enforcement..."
if grep -r "http://" app/ --include="*.ts" --include="*.tsx" | grep -v "localhost" | grep -v "127.0.0.1"; then
    echo -e "${YELLOW}⚠️  HTTP URLs found in code (should use HTTPS)${NC}"
fi

# 10. Summary
echo ""
echo "================================"
echo -e "${GREEN}✅ Security scan complete${NC}"
echo ""
echo "📋 Recommendations:"
echo "  1. Review and fix any warnings above"
echo "  2. Keep dependencies up to date"
echo "  3. Run security scans before each deployment"
echo "  4. Consider running Snyk or similar tools in CI/CD"
echo "  5. Review security documentation: SECURITY_AND_COMPLIANCE.md"
echo ""

exit 0
