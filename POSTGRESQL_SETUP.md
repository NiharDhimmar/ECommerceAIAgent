# PostgreSQL Database Setup Guide

This application now uses PostgreSQL as the primary database. Follow these steps to set up PostgreSQL:

## Option 1: Local PostgreSQL Installation

### Windows
1. **Download PostgreSQL**: Visit https://www.postgresql.org/download/windows/
2. **Install PostgreSQL**: Run the installer and follow the setup wizard
3. **Set Password**: Remember the password you set for the `postgres` user
4. **Start Service**: PostgreSQL service should start automatically

### macOS
```bash
# Using Homebrew
brew install postgresql
brew services start postgresql

# Or download from https://www.postgresql.org/download/macosx/
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

## Option 2: Cloud PostgreSQL Services

### Free Options:
- **Supabase**: https://supabase.com/ (Free tier available)
- **Railway**: https://railway.app/ (Free tier available)
- **Neon**: https://neon.tech/ (Free tier available)

### Paid Options:
- **AWS RDS**: https://aws.amazon.com/rds/postgresql/
- **Heroku Postgres**: https://www.heroku.com/postgres
- **Google Cloud SQL**: https://cloud.google.com/sql/docs/postgres

## Database Configuration

### Environment Variables
Set these environment variables in your `.env` file:

```env
# Option 1: Full DATABASE_URL
DATABASE_URL=postgresql://username:password@host:port/database_name

# Option 2: Individual parameters
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voiceai
DB_USER=postgres
DB_PASSWORD=your_password
```

### Example Configurations

#### Local PostgreSQL:
```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/voiceai
```

#### Supabase:
```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

#### Railway:
```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@[YOUR-HOST]:[YOUR-PORT]/railway
```

## Database Setup

### Create Database (if needed)
```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create database
CREATE DATABASE voiceai;

-- Create user (optional)
CREATE USER voiceai_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE voiceai TO voiceai_user;
```

### Tables
The application will automatically create the required tables:
- `transcripts` - Stores call transcripts and intent analysis
- `recordings` - Stores recording metadata

## Testing Connection

Run the test script to verify your PostgreSQL connection:
```bash
python test_postgres_connection.py
```

## Troubleshooting

### Connection Refused
- Ensure PostgreSQL service is running
- Check if port 5432 is open
- Verify firewall settings

### Authentication Failed
- Check username and password
- Verify database name exists
- Ensure user has proper permissions

### SSL Issues (Cloud Databases)
- Add `?sslmode=require` to your DATABASE_URL
- Example: `postgresql://user:pass@host:port/db?sslmode=require`

## Migration from SQLite

If you have existing data in SQLite, you can migrate it:

1. Export data from SQLite:
```bash
sqlite3 voiceai.db ".dump" > backup.sql
```

2. Import to PostgreSQL (after creating tables):
```bash
psql -U postgres -d voiceai -f backup.sql
```

## Next Steps

1. Set up PostgreSQL (local or cloud)
2. Configure environment variables
3. Test connection with `python test_postgres_connection.py`
4. Start the application: `python app.py`
5. Access the dashboard at `http://localhost:3000`
