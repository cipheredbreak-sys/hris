# 🚀 HRIS Setup & Troubleshooting Guide

Quick setup guide to get both backend and frontend running smoothly.

## 🛠 Prerequisites

### Required Software
- **Python 3.8+** - [Download here](https://www.python.org/downloads/)
- **Node.js 16+** - [Download here](https://nodejs.org/)
- **Git** (optional but recommended)

### Verify Prerequisites
```bash
python3 --version  # Should show 3.8+
node --version     # Should show 16+
npm --version      # Should show 6+
```

## ⚡ Quick Setup (Automated)

Run the automated setup script:

```bash
# Make script executable and run
chmod +x setup.sh
./setup.sh
```

This will:
- ✅ Set up Python virtual environment
- ✅ Install Django dependencies
- ✅ Set up database and run migrations
- ✅ Initialize RBAC system with admin user
- ✅ Install React dependencies
- ✅ Configure authentication system

## 🏃‍♂️ Start Servers

After setup, use the start script:

```bash
# Start both backend and frontend
./start.sh
```

Or start manually:

### Backend (Terminal 1)
```bash
source venv/bin/activate
python manage.py runserver 8080
```

### Frontend (Terminal 2)
```bash
cd broker-console-frontend
npm start
```

## 🌐 Access Points

Once running:

- **🔗 Backend Admin**: http://localhost:8080/admin/
- **🔗 Authentication**: http://localhost:8080/accounts/login/
- **🔗 API Documentation**: http://localhost:8080/swagger/
- **🔗 Frontend App**: http://localhost:3000/

### Default Credentials
- **Email**: admin@hris.com  
- **Password**: Admin123!@#

## 🐛 Troubleshooting

### Backend Issues

#### 1. "ModuleNotFoundError: No module named 'django'"
**Problem**: Django not installed or virtual environment not activated

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

#### 2. "Port 8080 already in use"
**Solution**: Use a different port
```bash
python manage.py runserver 8081
```

#### 3. Database migration errors
**Solution**: Reset database
```bash
# Delete database (SQLite)
rm db.sqlite3

# Recreate migrations
python manage.py makemigrations
python manage.py migrate

# Reinitialize RBAC
python manage.py init_rbac --create-superuser --create-sample-orgs
```

#### 4. "CSRF verification failed"
**Solution**: Check CORS settings in `.env`
```bash
cp .env.example .env
# Edit .env and add your frontend URL to CORS_ALLOWED_ORIGINS
```

#### 5. Social auth not working
**Solution**: Configure OAuth apps
```bash
python manage.py setup_social_apps --update-site
```

### Frontend Issues

#### 1. "npm: command not found"
**Problem**: Node.js not installed

**Solution**: Install Node.js from https://nodejs.org/

#### 2. "Module not found" errors
**Solution**: Install dependencies
```bash
cd broker-console-frontend
rm -rf node_modules package-lock.json
npm install
```

#### 3. "Port 3000 already in use"
**Solution**: 
- Kill existing process: `lsof -ti:3000 | xargs kill`
- Or use different port: `PORT=3001 npm start`

#### 4. React compilation errors
**Solution**: Clear cache and reinstall
```bash
cd broker-console-frontend
npm start -- --reset-cache
```

#### 5. TypeScript errors
**Solution**: Check TypeScript configuration
```bash
# Ensure TypeScript version is compatible
npm install typescript@^4.9.5
```

### Network Issues

#### 1. Backend/Frontend not communicating
**Solution**: Check CORS configuration

In `.env`:
```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

#### 2. API requests failing
**Solution**: Verify backend is running and accessible
```bash
# Test backend is running
curl http://localhost:8080/swagger/

# Check Django logs for errors
```

## 🔧 Manual Setup (If Automated Fails)

### Backend Setup
```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Environment setup
cp .env.example .env
# Edit .env as needed

# 5. Database setup
python manage.py makemigrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Initialize RBAC
python manage.py init_rbac

# 8. Start server
python manage.py runserver 8080
```

### Frontend Setup
```bash
# 1. Navigate to frontend directory
cd broker-console-frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm start
```

## 📝 Environment Configuration

### Backend (.env file)
```bash
# Copy example and edit
cp .env.example .env

# Key settings:
DEBUG=True
SECRET_KEY=your-secret-key
SITE_DOMAIN=localhost:8080
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Frontend Environment
Create `broker-console-frontend/.env`:
```bash
REACT_APP_API_BASE_URL=http://localhost:8080
REACT_APP_ENVIRONMENT=development
```

## 🧪 Testing Setup

### Test Backend
```bash
source venv/bin/activate
python manage.py test accounts.test_auth
```

### Test Frontend
```bash
cd broker-console-frontend
npm test
```

## 🔄 Reset Everything

If you need to start fresh:

```bash
# Backend reset
rm -rf venv db.sqlite3
rm -rf accounts/migrations/00*.py
rm -rf broker_console/migrations/00*.py

# Frontend reset  
cd broker-console-frontend
rm -rf node_modules package-lock.json build

# Run setup again
cd ..
./setup.sh
```

## 📊 System Requirements

### Minimum Requirements
- **RAM**: 4GB
- **Storage**: 2GB free space
- **OS**: macOS 10.15+, Ubuntu 18.04+, Windows 10+

### Recommended Requirements
- **RAM**: 8GB+
- **Storage**: 5GB+ free space
- **CPU**: Multi-core processor

## 🆘 Getting Help

### Log Locations
- **Django logs**: Console output where you ran `python manage.py runserver`
- **React logs**: Console output where you ran `npm start`
- **Browser logs**: F12 → Console tab

### Debug Mode
Enable detailed error messages:

**Backend**: Set `DEBUG=True` in `.env`  
**Frontend**: Errors shown in browser console

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Missing Python packages | `pip install -r requirements.txt` |
| `EADDRINUSE` | Port already in use | Use different port or kill process |
| `CORS error` | Cross-origin blocked | Update CORS settings |
| `404 Not Found` | Wrong URL/port | Check server is running |
| `500 Server Error` | Backend crash | Check Django logs |

## ✅ Success Checklist

After setup, verify these work:

- [ ] Backend admin panel loads: http://localhost:8080/admin/
- [ ] Can login with admin@hris.com / Admin123!@#
- [ ] API docs accessible: http://localhost:8080/swagger/
- [ ] Frontend loads: http://localhost:3000/
- [ ] No console errors in browser F12
- [ ] Backend and frontend can communicate

## 🎉 You're All Set!

If everything works, you should see:
- ✅ Django backend running on port 8080
- ✅ React frontend running on port 3000  
- ✅ Authentication system functional
- ✅ Admin panel accessible
- ✅ No error messages

Happy coding! 🚀