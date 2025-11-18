# PRM Dashboard - Administrator Guide

Complete guide for system administrators managing the PRM Dashboard.

## Table of Contents

1. [Administrator Overview](#administrator-overview)
2. [User Management](#user-management)
3. [Organization Settings](#organization-settings)
4. [Security Management](#security-management)
5. [Audit Logs](#audit-logs)
6. [System Monitoring](#system-monitoring)
7. [Data Management](#data-management)
8. [Integration Management](#integration-management)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

## Administrator Overview

### Administrator Responsibilities

As a system administrator, you are responsible for:
- ✅ User account management
- ✅ Security and access control
- ✅ System configuration
- ✅ Monitoring and performance
- ✅ Data backup and recovery
- ✅ Compliance and audit
- ✅ Integration management
- ✅ User support and training

### Administrator Permissions

Administrators have access to:
- All user management functions
- System settings and configuration
- Audit logs and reports
- Security settings
- Data export/import
- Integration configuration

## User Management

### Creating User Accounts

1. **Navigate to Settings → Users**
2. Click "Add User"
3. Enter user information:
   - Email address (required, used for login)
   - Full name
   - Role (admin, provider, staff, patient)
   - Department
   - Permissions
4. Click "Create User"
5. User receives email with login instructions

### User Roles

**Admin:**
- Full system access
- User management
- Configuration changes
- All permissions granted automatically

**Provider:**
- Patient care functions
- Appointment management
- Journey management
- Communication tools
- Limited settings access

**Staff:**
- Administrative functions
- Appointment scheduling
- Patient registration
- Communication tools
- No clinical access

**Patient:**
- Personal health information
- Appointment viewing
- Message healthcare team
- Journey progress tracking

### Managing Permissions

Granular permissions can be assigned:

**Patient Permissions:**
- `patient.view` - View patient information
- `patient.create` - Create patient records
- `patient.update` - Update patient information
- `patient.delete` - Delete patient records
- `patient.search` - Search patient database

**Appointment Permissions:**
- `appointment.view`
- `appointment.create`
- `appointment.update`
- `appointment.cancel`
- `appointment.reschedule`

**Journey Permissions:**
- `journey.view`
- `journey.create`
- `journey.update`
- `journey.complete`

**Communication Permissions:**
- `communication.send`
- `communication.view`
- `communication.bulk` (requires extra caution)

**Ticket Permissions:**
- `ticket.view`
- `ticket.create`
- `ticket.update`
- `ticket.assign`
- `ticket.resolve`

### Deactivating Users

1. Navigate to Settings → Users
2. Find the user
3. Click "Deactivate"
4. Confirm action
5. User loses access immediately
6. Data is retained per retention policy

### Password Reset

**For Users:**
1. Find user in user list
2. Click "Reset Password"
3. User receives reset email

**Temporary Password:**
1. Click "Generate Temporary Password"
2. Provide to user securely
3. User must change on first login

## Organization Settings

### General Settings

**Organization Profile:**
- Organization name
- Address and contact information
- Logo upload
- Timezone
- Language preference

**Date & Time Formats:**
- Date format (MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD)
- Time format (12-hour, 24-hour)
- Week start day

### AI Configuration

**OpenAI Integration:**
1. Navigate to Settings → AI Assistant
2. Enter OpenAI API key
3. Configure settings:
   - Enable/disable AI features
   - Auto-suggestions
   - Confirmation for high-risk actions
   - Maximum retry attempts
4. Save configuration

**AI System Status:**
- View active agents (5 total)
- View registered tools (30 total)
- Monitor AI usage
- Review AI-generated actions

### Notification Settings

**Email Configuration:**
- SMTP server settings
- From address
- Email templates
- Delivery testing

**SMS Configuration:**
- Provider (Twilio, etc.)
- API credentials
- Phone number
- Message templates

**WhatsApp Configuration:**
- Business account
- API credentials
- Message templates
- Webhook configuration

### Branding

**Customize Appearance:**
- Upload logo
- Set primary color
- Set secondary color
- Configure email templates with branding

## Security Management

### Access Control

**Session Settings:**
- Session timeout (default: 30 minutes)
- Warning before timeout (default: 5 minutes)
- Maximum session duration (default: 8 hours)
- Concurrent session limit

**Password Policy:**
- Minimum length (default: 12 characters)
- Complexity requirements
- Password expiration (default: 90 days)
- Password history (prevent reuse)

**Two-Factor Authentication:**
- Enable/disable MFA
- Enforce for all users or specific roles
- MFA methods (SMS, authenticator app)

### Rate Limiting

**Login Protection:**
- Max attempts: 5 per 15 minutes
- Block duration: 30 minutes
- Account lockout after: 10 failed attempts in 24 hours

**API Rate Limits:**
- Requests per minute: 100
- Burst allowance: 150
- Throttle response: 429 status code

### IP Whitelisting

1. Navigate to Settings → Security → IP Whitelist
2. Click "Add IP Range"
3. Enter IP address or CIDR range
4. Provide description
5. Save

**Example:**
```
192.168.1.0/24 - Office network
10.0.0.100 - VPN server
```

### Security Headers

Configured in `next.config.js`:
- Strict-Transport-Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy
- Content-Security-Policy

### Data Encryption

**At Rest:**
- AES-256-GCM encryption for PHI
- Encryption keys managed securely
- Key rotation: Quarterly

**In Transit:**
- TLS 1.3 required
- Certificate pinning
- Perfect forward secrecy

## Audit Logs

### Accessing Audit Logs

1. Navigate to Settings → Audit Logs
2. Filter by:
   - Date range
   - User
   - Action type
   - Resource type
   - Severity level

### Audit Log Types

**Critical Events:**
- Failed login attempts
- Password changes
- Data exports
- User deletions
- Permission changes

**High Priority:**
- Patient record creation
- Patient record updates
- Bulk communications
- Ticket assignments

**Medium Priority:**
- Patient record viewing
- Appointment cancellations
- Journey completion

**Low Priority:**
- Dashboard views
- List queries
- Settings views

### Log Retention

- **Audit logs**: 6 years (HIPAA requirement)
- **System logs**: 1 year
- **Access logs**: 6 months
- **Error logs**: 1 year

### Exporting Audit Logs

1. Navigate to Audit Logs
2. Set filters
3. Click "Export"
4. Choose format (CSV, JSON, PDF)
5. Download file

**Note:** All exports are logged for compliance.

### Reviewing Suspicious Activity

**Red Flags:**
- Multiple failed login attempts
- Access at unusual times
- Bulk data exports
- Permission changes
- Unusual access patterns

**Response:**
1. Identify affected user
2. Review complete activity log
3. Contact user for verification
4. Suspend account if necessary
5. Report to security officer
6. Document incident

## System Monitoring

### Dashboard Metrics

**User Activity:**
- Active users (last 24 hours)
- Peak usage times
- Average session duration
- Page views

**System Health:**
- API response times
- Error rates
- Database performance
- Cache hit rates

**Resource Usage:**
- CPU utilization
- Memory usage
- Disk space
- Network bandwidth

### Performance Monitoring

**Tools:**
- Built-in analytics (Settings → Analytics)
- Vercel Analytics (if deployed on Vercel)
- Custom monitoring integration

**Key Metrics:**
- Page load time (target: < 2 seconds)
- Time to interactive (target: < 3 seconds)
- API response time (target: < 500ms)
- Error rate (target: < 0.1%)

### Alerting

**Configure Alerts:**
1. Navigate to Settings → Alerts
2. Create alert rule:
   - Metric to monitor
   - Threshold value
   - Alert channels (email, SMS, webhook)
3. Save rule

**Recommended Alerts:**
- API error rate > 1%
- Response time > 2 seconds
- Failed logins > 10 in 5 minutes
- Disk space < 20%
- Database connection failures

### Error Tracking

**Integration with Sentry (Optional):**
1. Create Sentry project
2. Add DSN to environment variables
3. Errors automatically tracked
4. Receive email alerts

**Error Dashboard:**
- View error frequency
- Stack traces
- Affected users
- Browser/device information

## Data Management

### Data Backup

**Automated Backups:**
- Frequency: Daily at 2 AM UTC
- Retention: 30 days
- Location: Encrypted cloud storage
- Verification: Automated integrity checks

**Manual Backup:**
1. Navigate to Settings → Data Management
2. Click "Create Backup"
3. Wait for completion
4. Download backup file (encrypted)

### Data Restore

**From Backup:**
1. Navigate to Settings → Data Management
2. Click "Restore from Backup"
3. Select backup file
4. Choose restore options:
   - Full restore
   - Partial restore (specific tables)
5. Confirm action
6. System will be unavailable during restore
7. Verify data after restoration

**Estimated Downtime:**
- Small database (< 1GB): 5-10 minutes
- Medium database (1-10GB): 15-30 minutes
- Large database (> 10GB): 30-60 minutes

### Data Export

**Bulk Export:**
1. Navigate to Settings → Data Management
2. Click "Export Data"
3. Select data types:
   - Patients
   - Appointments
   - Journeys
   - Communications
   - Tickets
4. Choose format (CSV, JSON, XML)
5. Click "Export"
6. Download file

**Note:** Exports are logged and require admin permission.

### Data Import

**From CSV/JSON:**
1. Navigate to Settings → Data Management
2. Click "Import Data"
3. Select data type
4. Upload file
5. Map columns to fields
6. Validate data
7. Review errors
8. Click "Import"

**Best Practices:**
- Validate data format before import
- Backup before large imports
- Import during off-hours
- Test with sample data first

### Data Retention Policy

**Active Data:**
- Patients: Indefinite (until explicitly deleted)
- Appointments: 7 years after last activity
- Communications: 6 years
- Audit logs: 6 years (HIPAA requirement)

**Soft Deletion:**
- Data marked as deleted but retained
- Not shown in normal views
- Can be recovered within 30 days
- Permanently deleted after retention period

**Hard Deletion:**
- Permanent removal from database
- Cannot be recovered
- Requires explicit admin action
- Logged for compliance

## Integration Management

### API Access

**Creating API Keys:**
1. Navigate to Settings → API
2. Click "Create API Key"
3. Provide name and description
4. Set permissions
5. Set expiration date
6. Click "Create"
7. Copy API key (shown only once)

**API Key Management:**
- View active keys
- Revoke keys
- Monitor usage
- Set rate limits

### Webhooks

**Configuring Webhooks:**
1. Navigate to Settings → Webhooks
2. Click "Add Webhook"
3. Enter endpoint URL
4. Select events:
   - Patient created/updated
   - Appointment booked/cancelled
   - Journey completed
   - Communication sent
5. Set secret for verification
6. Test webhook
7. Save

**Webhook Security:**
- Use HTTPS endpoints only
- Verify webhook signatures
- Implement retry logic
- Monitor webhook failures

### Third-Party Integrations

**Available Integrations:**
- EHR systems (HL7/FHIR)
- Billing systems
- Lab systems
- Pharmacy systems
- Insurance verification

**Setup Process:**
1. Navigate to Settings → Integrations
2. Select integration type
3. Enter credentials
4. Configure mapping
5. Test connection
6. Enable integration

## Troubleshooting

### Common Issues

**Users Can't Log In:**
1. Check user account status (active/deactivated)
2. Verify email address is correct
3. Check for account lockout
4. Reset password
5. Review audit logs for failed attempts

**Slow Performance:**
1. Check system metrics
2. Review error logs
3. Check database performance
4. Verify network connectivity
5. Clear cache
6. Restart services if needed

**AI Assistant Not Working:**
1. Verify OpenAI API key is valid
2. Check API usage limits
3. Review error logs
4. Test with simple command
5. Contact support if persists

**Email/SMS Not Sending:**
1. Verify provider credentials
2. Check quota limits
3. Review bounce/failure logs
4. Test with admin account
5. Check spam filters

### System Logs

**Accessing Logs:**
```bash
# Application logs
tail -f /var/log/prm-dashboard/app.log

# Error logs
tail -f /var/log/prm-dashboard/error.log

# Access logs
tail -f /var/log/prm-dashboard/access.log

# Audit logs (via dashboard)
Settings → Audit Logs
```

**Log Levels:**
- DEBUG: Detailed information for debugging
- INFO: General informational messages
- WARN: Warning messages
- ERROR: Error events
- CRITICAL: Critical failures

### Support Escalation

**Level 1 - Self-Service:**
- Check documentation
- Review error messages
- Check system status page

**Level 2 - Support Team:**
- Email: support@healthtech.com
- Provide: Error message, screenshots, steps to reproduce

**Level 3 - Engineering:**
- Critical system failures
- Data corruption
- Security incidents
- Escalated via support team

## Maintenance

### Regular Maintenance Tasks

**Daily:**
- ✅ Review system health dashboard
- ✅ Check error logs
- ✅ Monitor user activity
- ✅ Verify backups completed

**Weekly:**
- ✅ Review audit logs
- ✅ Check failed login attempts
- ✅ Update documentation
- ✅ Review support tickets
- ✅ Test backup restoration
- ✅ Security patch check

**Monthly:**
- ✅ User access review
- ✅ Permission audit
- ✅ Performance review
- ✅ Update dependencies
- ✅ Capacity planning
- ✅ Compliance review

**Quarterly:**
- ✅ Security audit
- ✅ Disaster recovery drill
- ✅ User training
- ✅ Policy review
- ✅ Vendor review
- ✅ Encryption key rotation

**Annually:**
- ✅ Comprehensive security assessment
- ✅ Penetration testing
- ✅ Business continuity test
- ✅ Compliance certification
- ✅ Contract renewals

### System Updates

**Update Process:**
1. Review release notes
2. Test in staging environment
3. Schedule maintenance window
4. Notify users
5. Create backup
6. Deploy update
7. Verify functionality
8. Monitor for issues

**Rollback Plan:**
1. Restore from backup
2. Deploy previous version
3. Verify functionality
4. Notify users
5. Document issue
6. Plan remediation

### Maintenance Windows

**Scheduled Maintenance:**
- Frequency: Monthly (first Sunday, 2 AM - 6 AM)
- Notification: 1 week advance notice
- Duration: 2-4 hours
- Fallback: Rollback plan ready

**Emergency Maintenance:**
- Critical security patches
- Data integrity issues
- System failures
- Minimal notice (1 hour if possible)

## Best Practices

### Security Best Practices

1. **Principle of Least Privilege**
   - Grant minimum necessary permissions
   - Regular permission audits
   - Remove unused accounts

2. **Regular Updates**
   - Apply security patches promptly
   - Keep dependencies current
   - Test before production deployment

3. **Monitor and Alert**
   - Set up comprehensive alerting
   - Review logs regularly
   - Investigate anomalies

4. **Backup and Recovery**
   - Test backups regularly
   - Verify restore process
   - Keep offsite backups

### Operational Best Practices

1. **Documentation**
   - Keep runbooks current
   - Document all changes
   - Maintain configuration records

2. **Change Management**
   - Test in staging first
   - Have rollback plan
   - Communicate changes

3. **Monitoring**
   - Proactive monitoring
   - Performance baselines
   - Capacity planning

4. **User Training**
   - Regular training sessions
   - Updated documentation
   - Support resources

---

**Last Updated**: November 19, 2024
**Version**: 1.0
**For**: System Administrators

**Need Help?** Contact admin-support@healthtech.com
