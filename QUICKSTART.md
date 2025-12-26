# 🚀 Quick Start - AI Support Platform

Get the complete AI Support Platform running in **under 5 minutes** with all features enabled!

## 📋 Prerequisites

**Required:**
- Docker 20.10+ & Docker Compose 2.0+
- 8GB RAM minimum
- 20GB free disk space

**Optional (for training):**
- NVIDIA GPU with 8GB+ VRAM
- NVIDIA Docker runtime

## ⚡ Super Quick Start (One Command)

```bash
# Clone repository
git clone https://github.com/Marksio90/ai-support-platform.git
cd ai-support-platform

# Copy and edit environment file
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY

# Start everything!
cd deployment
./start.sh
```

That's it! 🎉

## 🔑 Configuration

### Minimum Required (.env file)

```bash
# OpenAI (for intelligent responses)
OPENAI_API_KEY=sk-proj-your-key-here

# Passwords (change these!)
MONGO_ROOT_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password
GRAFANA_ADMIN_PASSWORD=your_grafana_password
```

### Optional Features

```bash
# Enable A/B testing (compare rule-based vs OpenAI)
AB_TEST_ENABLED=true

# Enable automatic LoRA training (requires GPU)
ENABLE_TRAINING=true

# Email alerts
SMTP_ENABLED=true
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 🎯 Deployment Options

The `start.sh` script offers 4 deployment modes:

### 1. Full Deployment ⭐ (Recommended)
```bash
./start.sh
# Select option 1

```

**Includes:**
- ✅ Frontend (Next.js)
- ✅ Backend API
- ✅ OpenAI LLM
- ✅ RAG Service
- ✅ Databases (Redis + MongoDB)
- ✅ Monitoring (Prometheus + Grafana)
- ✅ LoRA Training (if GPU available)

### 2. Production
```bash
./start.sh
# Select option 2
```

**Includes:**
- Same as Full, minus training
- Production optimizations
- Nginx reverse proxy
- Resource limits

### 3. Development
```bash
./start.sh
# Select option 3
```

**Includes:**
- Basic services only
- Hot reload enabled
- No resource limits

### 4. Training Only
```bash
./start.sh
# Select option 4
```

**Runs:**
- LoRA fine-tuning only
- Saves model to volume
- Exits when complete

## 🌐 Access Points

Once deployed, access services at:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | N/A |
| **Backend API** | http://localhost:8000 | N/A |
| **API Docs** | http://localhost:8000/docs | N/A |
| **Grafana** | http://localhost:3001 | admin / (your password) |
| **Prometheus** | http://localhost:9090 | N/A |

## 📊 Features Overview

### AI Modes

The platform supports **3 AI modes**:

#### 1. Rule-Based (Default)
- Fast responses (<200ms)
- No API costs
- Works offline
- Template-based answers

#### 2. OpenAI GPT-4 (Recommended)
- Highly intelligent
- Context-aware
- Handles edge cases
- ~$0.002 per request

#### 3. LoRA Fine-tuned
- Domain-specific
- No API costs
- Requires GPU for training
- Best accuracy for your data

### A/B Testing

Compare performance between modes:

```bash
# Enable in .env
AB_TEST_ENABLED=true
AB_TEST_SPLIT_RATIO=0.5  # 50/50 split
```

View results:
```bash
curl http://localhost:8000/ab-test/stats
```

### Training

Train custom LoRA model:

```bash
# Enable in .env
ENABLE_TRAINING=true
TRAINING_EPOCHS=3

# Start with training profile
docker-compose -f docker-compose.full.yml --profile training up -d
```

Monitor progress:
```bash
docker-compose -f docker-compose.full.yml logs -f training-service
```

## 🔧 Common Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.full.yml logs -f

# Specific service
docker-compose -f docker-compose.full.yml logs -f backend
```

### Restart Services
```bash
# All
docker-compose -f docker-compose.full.yml restart

# Specific
docker-compose -f docker-compose.full.yml restart llm-service
```

### Stop Everything
```bash
docker-compose -f docker-compose.full.yml down

# Keep data
docker-compose -f docker-compose.full.yml down

# Remove all data
docker-compose -f docker-compose.full.yml down -v
```

### Check Status
```bash
docker-compose -f docker-compose.full.yml ps
```

## 🧪 Testing

### Test Frontend
```bash
# Open in browser
open http://localhost:3000

# Or test with curl
curl http://localhost:3000
```

### Test Backend API
```bash
# Health check
curl http://localhost:8000/health

# Ask a question
curl -X POST http://localhost:8000/support/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Jak mogę zwrócić produkt?"}'
```

### Test Individual Services
```bash
# LLM Service
curl http://localhost:8001/health

# RAG Service
curl http://localhost:8002/health
curl http://localhost:8002/stats
```

## 📈 Monitoring

### Prometheus Metrics

Visit http://localhost:9090 and query:

```promql
# Request rate
rate(support_ai_requests_total[5m])

# Response time (95th percentile)
histogram_quantile(0.95, support_ai_response_seconds)

# Confidence scores
support_ai_confidence_score
```

### Grafana Dashboards

1. Visit http://localhost:3001
2. Login: admin / (your password)
3. Import dashboard from `deployment/grafana_dashboard.json`

## 🐛 Troubleshooting

### Services won't start

```bash
# Check Docker daemon
docker ps

# Check logs
docker-compose -f docker-compose.full.yml logs

# Restart Docker
sudo systemctl restart docker
```

### OpenAI errors

```bash
# Verify API key
echo $OPENAI_API_KEY

# Check LLM service logs
docker-compose -f docker-compose.full.yml logs llm-service

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Training fails

```bash
# Check GPU availability
nvidia-smi

# Check training logs
docker-compose -f docker-compose.full.yml logs training-service

# Run training manually
docker exec -it ecommerce-support-training python train_simple.py
```

### Out of memory

```bash
# Check memory usage
docker stats

# Reduce batch size in .env
TRAINING_BATCH_SIZE=2  # Instead of 4

# Or limit service memory
# Edit docker-compose.full.yml:
# deploy:
#   resources:
#     limits:
#       memory: 1G
```

## 🔒 Security

### Before Production

1. **Change all passwords** in `.env`
2. **Set up SSL/TLS** (use Let's Encrypt)
3. **Configure firewall**
4. **Enable rate limiting**
5. **Review CORS origins**

### SSL Setup

```bash
# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy to deployment
sudo cp /etc/letsencrypt/live/yourdomain.com/*.pem deployment/ssl/

# Use production config
docker-compose -f docker-compose.full.yml \
               -f docker-compose.prod.yml up -d
```

## 📚 Next Steps

1. **Customize knowledge base** - Add your FAQs to `data/public/faq.json`
2. **Add training data** - Real customer dialogs in `data/synthetic/`
3. **Fine-tune model** - Run training with your data
4. **Set up monitoring** - Configure Grafana alerts
5. **Deploy to production** - Use `docker-compose.prod.yml`

## 🆘 Getting Help

- **Documentation:** [docs/](docs/)
- **Issues:** https://github.com/Marksio90/ai-support-platform/issues
- **Discussions:** GitHub Discussions

## 📝 What's Running?

When you run `./start.sh` with full deployment, here's what starts:

```
┌─────────────────────────────────────────────┐
│          Frontend (Next.js)                 │
│          http://localhost:3000              │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│          Backend API (FastAPI)              │
│          http://localhost:8000              │
└──────┬──────────────────────┬───────────────┘
       │                      │
       ▼                      ▼
┌─────────────┐      ┌─────────────────┐
│ LLM Service │      │  RAG Service    │
│   (OpenAI)  │      │   (FAISS)       │
│    :8001    │      │    :8002        │
└─────────────┘      └─────────────────┘
       │                      │
       └──────────┬───────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│              Databases                      │
│  Redis (cache)    MongoDB (logs)           │
└─────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│            Monitoring                       │
│  Prometheus :9090    Grafana :3001         │
└─────────────────────────────────────────────┘
```

**Optional (with training enabled):**
```
┌─────────────────────────────────────────────┐
│       Training Service (GPU)                │
│       Runs once, saves model                │
└─────────────────────────────────────────────┘
```

---

## 🎊 You're All Set!

Your AI Support Platform is now running with:
- ✅ Intelligent AI responses (OpenAI or rule-based)
- ✅ Document retrieval (RAG)
- ✅ Real-time monitoring
- ✅ A/B testing ready
- ✅ Training pipeline (optional)

**Start chatting at:** http://localhost:3000

Enjoy! 🚀
