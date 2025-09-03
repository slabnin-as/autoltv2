# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AutoLT v2 - Flask-based application for managing Jira tasks and Jenkins jobs with scheduling capabilities. Key features:
- Jira task synchronization and search
- Jenkins job management and triggered execution
- PostgreSQL database for persistent storage
- Web interface for viewing/editing data
- Scheduled job execution with cron-like syntax

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Database setup (if no migrations directory exists)
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run development server
python run.py

# Run with Gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:5000 run:app

# Flask shell with models pre-loaded
flask shell
```

## Architecture

Flask application using Blueprint pattern for modular organization:

### Application Factory (`app/__init__.py`)
- Creates Flask app with configuration
- Initializes SQLAlchemy and Flask-Migrate extensions
- Registers blueprints for main routes, tasks, and jobs

### Configuration Management (`config/config.py`)
- Environment-based config classes (Development, Production, Testing)
- Loads settings from environment variables via python-dotenv
- Supports Celery configuration for background tasks

### Models (`app/models/`)
- **JiraTask**: Stores Jira issue data with metadata tracking
- **JenkinsJob**: Manages Jenkins job definitions, schedules, and execution history
- Uses SQLAlchemy ORM with PostgreSQL backend

### Services (`app/services/`)
- **JiraService**: Handles Jira API integration using python-jira library
- **JenkinsService**: Manages Jenkins job triggering via python-jenkins
- **SchedulerService**: APScheduler-based background job scheduling with cron expressions

### Web Interface (`app/blueprints/`)
- **main**: Dashboard and general routes
- **tasks**: Jira task management endpoints  
- **jobs**: Jenkins job management endpoints
- Blueprint registration with URL prefixes (/tasks, /jobs)

## Key Dependencies

- Flask 2.3.3 with SQLAlchemy and Migrate for web framework and ORM
- python-jira 3.5.0 and python-jenkins 1.8.0 for external API integration
- APScheduler 3.10.4 for cron-based job scheduling
- Celery 5.3.1 + Redis for background task processing
- psycopg2-binary for PostgreSQL connectivity

## Configuration

Uses environment variables for external service credentials:
- JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
- JENKINS_URL, JENKINS_USERNAME, JENKINS_TOKEN  
- DATABASE_URL for PostgreSQL connection
- REDIS_URL for caching and Celery backend
- SECRET_KEY for Flask sessions
- FLASK_ENV for environment selection

## Database Schema

**PostgreSQL Production/Testing:**
- Uses `autoltv2` schema instead of `public`
- Connection configured with `search_path=autoltv2,public`
- All models automatically use the autoltv2 schema

**SQLite Development:**
- Uses default schema (no schema separation)
- Models conditionally apply schema based on database type

**Schema Configuration:**
- Set `DATABASE_URL=postgresql://user:pass@host/db?options=-csearch_path%3Dautoltv2%2Cpublic`
- Models automatically detect PostgreSQL and apply schema

## Application Startup

Entry point is `run.py` which:
- Creates app using factory pattern with environment-based config
- Initializes SchedulerService for background jobs
- Sets up shell context with database models
- Configures scheduled jobs on first request
- Runs on localhost:5000 in debug mode for development