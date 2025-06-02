-- Create database for n8n
CREATE DATABASE n8n_db;

-- Create database for application
CREATE DATABASE lma_db;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE n8n_db TO lma_user;
GRANT ALL PRIVILEGES ON DATABASE lma_db TO lma_user;
