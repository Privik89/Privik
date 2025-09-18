# Troubleshooting Guide

## Overview

This troubleshooting guide provides solutions to common issues encountered when using or deploying Privik. It covers both technical and user-facing problems with step-by-step resolution instructions.

## Quick Diagnostics

### System Health Check

```bash
# Check all services status
docker-compose ps

# Check API health
curl -f http://localhost:8000/health

# Check database connectivity
docker-compose exec privik-api python -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
print('Database connection successful')
"

# Check Redis connectivity
docker-compose exec privik-api python -c "
import redis
r = redis.from_url('$REDIS_URL')
print('Redis connection successful:', r.ping())
"
```

### Log Analysis

```bash
# View recent logs
docker-compose logs --tail=100 -f

# View specific service logs
docker-compose logs privik-api
docker-compose logs postgres
docker-compose logs redis

# Search for errors
docker-compose logs | grep -i error
docker-compose logs | grep -i exception
```

## Common Issues

### 1. Database Connection Issues

#### Problem: Cannot connect to database

**Symptoms:**
- API returns 500 errors
- Database connection timeout errors
- "Connection refused" errors

**Diagnosis:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test database connectivity
docker-compose exec privik-api python -c "
import psycopg2
try:
    conn = psycopg2.connect('$DATABASE_URL')
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

**Solutions:**

1. **Start PostgreSQL service:**
   ```bash
   docker-compose up -d postgres
   ```

2. **Check database configuration:**
   ```bash
   # Verify DATABASE_URL in .env file
   cat .env | grep DATABASE_URL
   ```

3. **Reset database:**
   ```bash
   # Stop services
   docker-compose down
   
   # Remove database volume
   docker volume rm privik_postgres_data
   
   # Restart services
   docker-compose up -d
   
   # Run migrations
   docker-compose exec privik-api alembic upgrade head
   ```

4. **Check database permissions:**
   ```bash
   # Connect to database
   docker-compose exec postgres psql -U privik -d privik
   
   # Check user permissions
   \du
   ```

#### Problem: Database migration failures

**Symptoms:**
- Migration errors during startup
- "Table already exists" errors
- "Column does not exist" errors

**Solutions:**

1. **Check migration status:**
   ```bash
   docker-compose exec privik-api alembic current
   docker-compose exec privik-api alembic history
   ```

2. **Reset migrations:**
   ```bash
   # Drop all tables
   docker-compose exec postgres psql -U privik -d privik -c "
   DROP SCHEMA public CASCADE;
   CREATE SCHEMA public;
   "
   
   # Run migrations
   docker-compose exec privik-api alembic upgrade head
   ```

3. **Manual migration fix:**
   ```bash
   # Mark migration as applied
   docker-compose exec privik-api alembic stamp head
   ```

### 2. Redis Connection Issues

#### Problem: Redis connection failures

**Symptoms:**
- Cache operations failing
- "Connection refused" to Redis
- Performance degradation

**Diagnosis:**
```bash
# Check Redis status
docker-compose ps redis

# Test Redis connectivity
docker-compose exec privik-api python -c "
import redis
try:
    r = redis.from_url('$REDIS_URL')
    print('Redis connection successful:', r.ping())
except Exception as e:
    print(f'Redis connection failed: {e}')
"
```

**Solutions:**

1. **Start Redis service:**
   ```bash
   docker-compose up -d redis
   ```

2. **Check Redis configuration:**
   ```bash
   # Verify REDIS_URL in .env file
   cat .env | grep REDIS_URL
   ```

3. **Clear Redis cache:**
   ```bash
   docker-compose exec redis redis-cli FLUSHALL
   ```

4. **Check Redis memory:**
   ```bash
   docker-compose exec redis redis-cli info memory
   ```

### 3. API Authentication Issues

#### Problem: HMAC authentication failures

**Symptoms:**
- 401 Unauthorized errors
- "Invalid signature" errors
- API requests being rejected

**Diagnosis:**
```bash
# Check API key configuration
cat .env | grep HMAC

# Test HMAC signature generation
docker-compose exec privik-api python -c "
from app.security.hmac_auth import generate_hmac_signature
import time
timestamp = str(int(time.time()))
signature = generate_hmac_signature(
    'GET', '/health', '', timestamp, 'test_nonce', 'your_secret'
)
print(f'Generated signature: {signature}')
"
```

**Solutions:**

1. **Verify API keys:**
   ```bash
   # Check .env file
   cat .env | grep -E "HMAC_API_KEY_ID|HMAC_API_SECRET"
   ```

2. **Regenerate API keys:**
   ```bash
   # Generate new keys
   python -c "
   import secrets
   print('HMAC_API_KEY_ID=' + secrets.token_urlsafe(16))
   print('HMAC_API_SECRET=' + secrets.token_urlsafe(32))
   "
   ```

3. **Check timestamp synchronization:**
   ```bash
   # Verify system time
   date
   # Ensure system time is synchronized
   ```

#### Problem: JWT token issues

**Symptoms:**
- Frontend login failures
- "Token expired" errors
- Session timeout issues

**Solutions:**

1. **Check JWT secret:**
   ```bash
   cat .env | grep JWT_SECRET
   ```

2. **Clear browser storage:**
   ```javascript
   // In browser console
   localStorage.clear();
   sessionStorage.clear();
   ```

3. **Regenerate JWT secret:**
   ```bash
   python -c "
   import secrets
   print('JWT_SECRET=' + secrets.token_urlsafe(32))
   "
   ```

### 4. Email Integration Issues

#### Problem: Gmail integration not working

**Symptoms:**
- No emails being processed
- "Authentication failed" errors
- Integration status shows "disconnected"

**Diagnosis:**
```bash
# Check integration status
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/ui/integrations/status

# Check Gmail API logs
docker-compose logs privik-api | grep -i gmail
```

**Solutions:**

1. **Refresh Gmail token:**
   ```bash
   # Go to Gmail integration settings
   # Click "Reconnect" button
   # Complete OAuth flow
   ```

2. **Check Gmail API quotas:**
   - Verify Gmail API is enabled
   - Check API quota limits
   - Monitor quota usage

3. **Verify Gmail permissions:**
   - Ensure proper OAuth scopes
   - Check user consent
   - Verify domain-wide delegation

#### Problem: Microsoft 365 integration issues

**Symptoms:**
- O365 emails not being fetched
- "Insufficient privileges" errors
- Graph API errors

**Solutions:**

1. **Check tenant configuration:**
   ```bash
   cat .env | grep O365_TENANT_ID
   ```

2. **Verify Graph API permissions:**
   - Check application permissions in Azure AD
   - Ensure Mail.Read permissions
   - Verify admin consent

3. **Test Graph API connectivity:**
   ```bash
   curl -H "Authorization: Bearer $GRAPH_TOKEN" \
     https://graph.microsoft.com/v1.0/me/messages
   ```

### 5. Sandbox Analysis Issues

#### Problem: CAPEv2 connection failures

**Symptoms:**
- Sandbox analysis not working
- "Connection timeout" errors
- Analysis tasks stuck in "pending" state

**Diagnosis:**
```bash
# Check CAPE connectivity
curl -f $CAPE_BASE_URL/api/tasks/list

# Check sandbox status
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/ui/sandbox/status
```

**Solutions:**

1. **Verify CAPE configuration:**
   ```bash
   cat .env | grep CAPE
   ```

2. **Check CAPE service status:**
   ```bash
   # If using Docker
   docker-compose ps cape
   
   # Check CAPE logs
   docker-compose logs cape
   ```

3. **Test CAPE API:**
   ```bash
   curl -H "Authorization: Bearer $CAPE_API_TOKEN" \
     $CAPE_BASE_URL/api/tasks/list
   ```

#### Problem: Sandbox analysis timeouts

**Symptoms:**
- Analysis tasks taking too long
- Tasks stuck in "running" state
- Memory or CPU issues

**Solutions:**

1. **Check system resources:**
   ```bash
   # Check CPU and memory usage
   docker stats
   
   # Check disk space
   df -h
   ```

2. **Adjust timeout settings:**
   ```bash
   # In .env file
   SANDBOX_TIMEOUT=300  # 5 minutes
   SANDBOX_MEMORY_LIMIT=2048  # 2GB
   ```

3. **Restart sandbox services:**
   ```bash
   docker-compose restart cape
   ```

### 6. Frontend Issues

#### Problem: Frontend not loading

**Symptoms:**
- Blank page or loading errors
- JavaScript errors in console
- API connection failures

**Diagnosis:**
```bash
# Check frontend service
docker-compose ps privik-frontend

# Check frontend logs
docker-compose logs privik-frontend

# Test API connectivity from frontend
curl -f http://localhost:8000/health
```

**Solutions:**

1. **Rebuild frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   docker-compose up -d --build privik-frontend
   ```

2. **Check environment variables:**
   ```bash
   cat .env | grep REACT_APP
   ```

3. **Clear browser cache:**
   - Hard refresh (Ctrl+F5)
   - Clear browser cache
   - Disable browser extensions

#### Problem: API proxy issues

**Symptoms:**
- Frontend cannot reach API
- CORS errors
- 404 errors for API endpoints

**Solutions:**

1. **Check nginx configuration:**
   ```bash
   # Verify nginx config
   docker-compose exec nginx nginx -t
   
   # Check nginx logs
   docker-compose logs nginx
   ```

2. **Update API URL:**
   ```bash
   # In .env file
   REACT_APP_API_URL=http://localhost:8000
   ```

3. **Check CORS settings:**
   ```python
   # In backend/app/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### 7. Performance Issues

#### Problem: Slow email processing

**Symptoms:**
- High response times
- Email processing delays
- System resource exhaustion

**Diagnosis:**
```bash
# Check system resources
docker stats

# Check database performance
docker-compose exec postgres psql -U privik -d privik -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"

# Check Redis performance
docker-compose exec redis redis-cli --latency-history -i 1
```

**Solutions:**

1. **Optimize database:**
   ```bash
   # Add database indexes
   docker-compose exec privik-api python -c "
   from app.database.optimization import create_indexes
   from app.database import get_db
   db = next(get_db())
   create_indexes(db)
   "
   ```

2. **Increase system resources:**
   ```yaml
   # In docker-compose.yml
   services:
     privik-api:
       deploy:
         resources:
           limits:
             memory: 2G
             cpus: '1.0'
   ```

3. **Enable caching:**
   ```bash
   # Check Redis cache usage
   docker-compose exec redis redis-cli info memory
   ```

#### Problem: High memory usage

**Symptoms:**
- Out of memory errors
- System slowdown
- Container restarts

**Solutions:**

1. **Monitor memory usage:**
   ```bash
   # Check container memory usage
   docker stats --no-stream
   
   # Check system memory
   free -h
   ```

2. **Optimize memory settings:**
   ```bash
   # In .env file
   DB_POOL_SIZE=10
   REDIS_MAX_MEMORY=512mb
   ```

3. **Restart services:**
   ```bash
   docker-compose restart
   ```

### 8. SSL/TLS Issues

#### Problem: SSL certificate errors

**Symptoms:**
- "Certificate not trusted" errors
- HTTPS connection failures
- Mixed content warnings

**Solutions:**

1. **Check certificate validity:**
   ```bash
   openssl x509 -in ssl/cert.pem -text -noout
   ```

2. **Generate new certificates:**
   ```bash
   # Generate self-signed certificate
   openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem \
     -out ssl/cert.pem -days 365 -nodes
   ```

3. **Update nginx configuration:**
   ```nginx
   server {
       listen 443 ssl http2;
       ssl_certificate /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;
   }
   ```

## Advanced Troubleshooting

### Database Performance Issues

#### Slow Query Analysis

```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

-- Analyze slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public';
```

#### Database Maintenance

```sql
-- Analyze tables
ANALYZE;

-- Vacuum tables
VACUUM ANALYZE;

-- Reindex tables
REINDEX DATABASE privik;
```

### Redis Performance Issues

#### Memory Analysis

```bash
# Check memory usage
redis-cli info memory

# Check key distribution
redis-cli --bigkeys

# Monitor commands
redis-cli monitor
```

#### Cache Optimization

```bash
# Clear specific cache patterns
redis-cli --scan --pattern "email_analysis:*" | xargs redis-cli del

# Set memory policy
redis-cli config set maxmemory-policy allkeys-lru
```

### Network Troubleshooting

#### Connectivity Testing

```bash
# Test internal connectivity
docker-compose exec privik-api ping postgres
docker-compose exec privik-api ping redis
docker-compose exec privik-api ping minio

# Test external connectivity
docker-compose exec privik-api ping google.com
docker-compose exec privik-api nslookup api.virustotal.com
```

#### Port Analysis

```bash
# Check listening ports
netstat -tlnp

# Check port connectivity
telnet localhost 8000
telnet localhost 5432
telnet localhost 6379
```

## Log Analysis

### Log Locations

```bash
# Application logs
docker-compose logs privik-api

# Database logs
docker-compose logs postgres

# Redis logs
docker-compose logs redis

# Nginx logs
docker-compose logs nginx

# System logs
journalctl -u docker
```

### Log Filtering

```bash
# Filter by error level
docker-compose logs privik-api | grep -i error

# Filter by time
docker-compose logs --since="2024-01-15T10:00:00" privik-api

# Filter by specific text
docker-compose logs privik-api | grep "email_processing"
```

### Log Rotation

```bash
# Configure log rotation
sudo nano /etc/logrotate.d/privik

# Log rotation configuration
/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
```

## Recovery Procedures

### Database Recovery

#### Backup Restoration

```bash
# Stop services
docker-compose down

# Restore from backup
docker-compose exec postgres psql -U privik -d privik < backup.sql

# Start services
docker-compose up -d
```

#### Point-in-Time Recovery

```bash
# Create base backup
pg_basebackup -D /backup/base -Ft -z -P

# Restore to specific time
pg_restore --clean --if-exists -d privik backup.dump
```

### System Recovery

#### Complete System Reset

```bash
# Stop all services
docker-compose down

# Remove all volumes
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Rebuild from scratch
docker-compose up -d --build
```

#### Configuration Reset

```bash
# Reset configuration files
git checkout .env
git checkout docker-compose.yml

# Regenerate secrets
python -c "
import secrets
print('HMAC_API_KEY_ID=' + secrets.token_urlsafe(16))
print('HMAC_API_SECRET=' + secrets.token_urlsafe(32))
print('JWT_SECRET=' + secrets.token_urlsafe(32))
"
```

## Getting Help

### Support Channels

1. **Documentation**: Check this troubleshooting guide first
2. **GitHub Issues**: Report bugs and request features
3. **Community Forum**: Ask questions and share solutions
4. **Email Support**: support@privik.com for urgent issues
5. **Phone Support**: +1-800-PRIVIK-1 for critical problems

### Information to Provide

When seeking help, please provide:

1. **System Information**:
   - Operating system and version
   - Docker version
   - Python version
   - Node.js version

2. **Configuration**:
   - Relevant .env settings (without secrets)
   - Docker Compose configuration
   - Error messages and logs

3. **Steps to Reproduce**:
   - Exact commands run
   - Expected vs actual behavior
   - Screenshots if applicable

4. **Logs**:
   - Relevant log entries
   - Error stack traces
   - System logs

### Emergency Contacts

- **Critical Security Issues**: security@privik.com
- **System Outages**: ops@privik.com
- **Data Loss**: recovery@privik.com

This troubleshooting guide should help resolve most common issues. For additional support, please contact the Privik support team with detailed information about your specific problem.
