# Production Deployment Guide

Complete guide for deploying the AI Support Platform to production.

## Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/ai-support-platform.git
cd ai-support-platform

# Setup environment variables
cp .env.example .env
# Edit .env with your settings

# Deploy with production config
cd deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Deployment Options](#deployment-options)
4. [SSL/TLS Setup](#ssltls-setup)
5. [Monitoring](#monitoring)
6. [Backup & Recovery](#backup--recovery)
7. [Scaling](#scaling)

---

## Prerequisites

### Hardware Requirements

**Minimum (Rule-based LLM):**
- 2 CPU cores
- 4GB RAM
- 20GB storage
- Can run on CPU-only server

**Recommended (OpenAI Integration):**
- 4 CPU cores
- 8GB RAM
- 50GB storage

**For LoRA Training:**
- NVIDIA GPU with 8GB+ VRAM
- 16GB RAM
- 100GB storage

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Domain name (for SSL)
- SSL certificate (Let's Encrypt recommended)

---

## Environment Configuration

### 1. Create `.env` File

```bash
# Copy template
cp .env.example .env
```

### 2. Configure Variables

```bash
# Database
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=your_strong_password_here

# Grafana
GRAFANA_ADMIN_PASSWORD=your_grafana_password

# OpenAI (optional - for OpenAI LLM)
OPENAI_API_KEY=sk-...

# Email (for Grafana alerts)
SMTP_HOST=smtp.gmail.com:587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# A/B Testing
AB_TEST_ENABLED=false

# Domain
DOMAIN=yourdomain.com
```

---

## Deployment Options

### Option 1: Rule-Based LLM (Default)

Lightweight, CPU-only deployment:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Features:**
- ✅ No API costs
- ✅ Fast responses (<200ms)
- ✅ Works offline
- ⚠️  Template-based (less flexible)

### Option 2: OpenAI Integration

Uses GPT-4 for intelligent responses:

```bash
# Set API key
export OPENAI_API_KEY=sk-...

# Deploy with OpenAI
docker-compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               -f docker-compose.openai.yml up -d
```

**Features:**
- ✅ Highly intelligent responses
- ✅ Learns from context
- ✅ Handles edge cases
- ⚠️  API costs (~$0.002/request)
- ⚠️  Requires internet

### Option 3: LoRA Fine-tuned Model

Custom-trained model for your domain:

```bash
# 1. Train model (requires GPU)
cd llm
bash ../scripts/setup_training.sh
python train_simple.py

# 2. Deploy with fine-tuned model
cd ../deployment
docker-compose -f docker-compose.yml \
               -f docker-compose.prod.yml up -d
```

**Features:**
- ✅ Domain-specific knowledge
- ✅ No API costs
- ✅ Complete control
- ⚠️  Requires GPU for training
- ⚠️  Longer initial setup

---

## SSL/TLS Setup

### Option 1: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem deployment/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem deployment/ssl/

# Update nginx.conf with your domain
sed -i 's/yourdomain.com/youractual domain.com/g' deployment/nginx.conf

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Option 2: CloudFlare

1. Point domain to your server IP
2. Enable CloudFlare proxy
3. SSL mode: "Full (strict)"
4. No nginx changes needed

---

## Monitoring

### Prometheus Metrics

Access at: `https://prometheus.yourdomain.com`

Key metrics:
- `support_ai_requests_total` - Total requests
- `support_ai_response_seconds` - Response times
- `support_ai_confidence_score` - Confidence distribution

### Grafana Dashboards

Access at: `https://grafana.yourdomain.com`

Default login:
- Username: `admin`
- Password: (set in `.env`)

Import dashboard: `/deployment/grafana_dashboard.json`

### Alerts Setup

Configure in Grafana:

1. **High Error Rate:**
   ```
   rate(support_ai_requests_total{status="error"}[5m]) > 0.1
   ```

2. **Low Confidence:**
   ```
   avg(support_ai_confidence_score) < 0.6
   ```

3. **Service Down:**
   ```
   up{job="backend"} == 0
   ```

---

## Backup & Recovery

### Automated Backups

```bash
# Create backup script
cat > /root/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups

# MongoDB backup
docker exec ecommerce-support-mongodb mongodump \
  --archive=/backup/mongodb_$DATE.archive

# Redis backup
docker exec ecommerce-support-redis redis-cli SAVE
docker cp ecommerce-support-redis:/data/dump.rdb \
  $BACKUP_DIR/redis_$DATE.rdb

# RAG vectorstore
docker cp ecommerce-support-rag:/app/vectorstore \
  $BACKUP_DIR/vectorstore_$DATE

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*_*" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /root/backup.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /root/backup.sh" | crontab -
```

### Recovery

```bash
# Restore MongoDB
docker cp mongodb_backup.archive ecommerce-support-mongodb:/backup/
docker exec ecommerce-support-mongodb mongorestore \
  --archive=/backup/mongodb_backup.archive

# Restore Redis
docker cp redis_backup.rdb ecommerce-support-redis:/data/dump.rdb
docker restart ecommerce-support-redis

# Restore RAG vectorstore
docker cp vectorstore_backup ecommerce-support-rag:/app/vectorstore
docker restart ecommerce-support-rag
```

---

## Scaling

### Horizontal Scaling

For high traffic, scale services:

```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 3

  llm-service:
    deploy:
      replicas: 2

  rag-service:
    deploy:
      replicas: 2
```

Deploy:
```bash
docker-compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               -f docker-compose.scale.yml up -d
```

### Load Balancing

Nginx automatically load balances across replicas.

For external load balancer:
```nginx
upstream backend {
    server backend1.yourdomain.com:8000;
    server backend2.yourdomain.com:8000;
    server backend3.yourdomain.com:8000;
}
```

### Database Scaling

**MongoDB Replica Set:**
```bash
# Init replica set
docker exec -it ecommerce-support-mongodb mongo --eval "
rs.initiate({
  _id: 'rs0',
  members: [
    {_id: 0, host: 'mongodb1:27017'},
    {_id: 1, host: 'mongodb2:27017'},
    {_id: 2, host: 'mongodb3:27017'}
  ]
})
"
```

**Redis Cluster:**
```bash
# Use Redis Cluster mode
# Update docker-compose.yml with redis-cluster image
```

---

## Performance Tuning

### Backend Optimization

```python
# app/main.py
@app.middleware("http")
async def add_cache_header(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "public, max-age=60"
    return response
```

### Database Indexing

```javascript
// MongoDB indexes
db.queries.createIndex({ "timestamp": -1 })
db.queries.createIndex({ "category": 1 })
db.queries.createIndex({ "confidence": 1 })
```

### CDN Integration

Use CloudFlare, AWS CloudFront, or similar for:
- Static assets
- Frontend caching
- DDoS protection

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs -f backend
docker-compose logs -f llm-service

# Check resources
docker stats

# Restart service
docker-compose restart backend
```

### High Memory Usage

```bash
# Check memory per service
docker stats --no-stream

# Limit memory in docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
```

### Slow Responses

1. Check Prometheus metrics
2. Enable Redis caching
3. Scale services
4. Optimize RAG index

---

## Security Checklist

- [ ] Change default passwords
- [ ] Enable SSL/TLS
- [ ] Configure firewall (UFW)
- [ ] Enable rate limiting
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] API key rotation
- [ ] Monitor access logs

---

## Support

**Issues:** https://github.com/yourusername/ai-support-platform/issues
**Docs:** https://yourdomain.com/docs
**Email:** support@yourcompany.com

---

**Last updated:** 2025-12-26
