-- PostgreSQL Database Initialization for Invoice OCR System
-- This script sets up the initial database structure

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database (if running manually, not needed in Docker)
-- CREATE DATABASE invoice_db;

-- Create user (if running manually, not needed in Docker)
-- CREATE USER invoice_user WITH ENCRYPTED PASSWORD 'invoice_pass_123';
-- GRANT ALL PRIVILEGES ON DATABASE invoice_db TO invoice_user;

-- Connect to the database
\c invoice_db;

-- Grant privileges to the user
GRANT ALL ON SCHEMA public TO invoice_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO invoice_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO invoice_user;

-- Create tables will be handled by SQLAlchemy, but we can add some initial data

-- Insert sample data after tables are created (this will be done by the application)
-- We'll create this as a function that can be called later

CREATE OR REPLACE FUNCTION insert_sample_data()
RETURNS void AS $$
BEGIN
    -- This function can be called after the application creates tables
    -- to insert some sample data for testing
    
    -- Example: INSERT INTO companies (name, tax_number) VALUES ('Sample Company', '1234567890');
    
    RAISE NOTICE 'Sample data insertion function created. Call this after tables are created by the application.';
END;
$$ LANGUAGE plpgsql;

-- Create indexes for better performance (will be added after table creation)
CREATE OR REPLACE FUNCTION create_performance_indexes()
RETURNS void AS $$
BEGIN
    -- Create indexes for common queries
    -- These will be executed after SQLAlchemy creates the tables
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'invoices') THEN
        -- Index for invoice number searches
        CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number);
        
        -- Index for date range queries
        CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);
        
        -- Index for company searches
        CREATE INDEX IF NOT EXISTS idx_invoices_company ON invoices(company_name);
        
        -- Index for status filtering
        CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
        
        -- Composite index for common filters
        CREATE INDEX IF NOT EXISTS idx_invoices_status_date ON invoices(status, created_at);
        
        RAISE NOTICE 'Performance indexes created successfully.';
    ELSE
        RAISE NOTICE 'Tables not yet created by SQLAlchemy. Run this function after application startup.';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to get database statistics
CREATE OR REPLACE FUNCTION get_invoice_stats()
RETURNS TABLE (
    total_invoices BIGINT,
    processed_invoices BIGINT,
    validated_invoices BIGINT,
    sent_to_erp BIGINT,
    error_invoices BIGINT,
    avg_confidence NUMERIC
) AS $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'invoices') THEN
        RETURN QUERY
        SELECT 
            COUNT(*) as total_invoices,
            COUNT(*) FILTER (WHERE status = 'ocr_processed') as processed_invoices,
            COUNT(*) FILTER (WHERE status = 'validated') as validated_invoices,
            COUNT(*) FILTER (WHERE status = 'sent_to_erp') as sent_to_erp,
            COUNT(*) FILTER (WHERE status = 'error') as error_invoices,
            ROUND(AVG(confidence_score), 3) as avg_confidence
        FROM invoices;
    ELSE
        -- Return zeros if table doesn't exist yet
        RETURN QUERY SELECT 0::BIGINT, 0::BIGINT, 0::BIGINT, 0::BIGINT, 0::BIGINT, 0.0::NUMERIC;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Log table for database operations
CREATE TABLE IF NOT EXISTS db_logs (
    id SERIAL PRIMARY KEY,
    operation VARCHAR(50) NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial log
INSERT INTO db_logs (operation, details) VALUES 
('DB_INIT', 'Database initialization completed successfully');

-- Display success message
DO $$ 
BEGIN 
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Invoice OCR Database Initialization Complete';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Database: invoice_db';
    RAISE NOTICE 'User: invoice_user'; 
    RAISE NOTICE 'Status: Ready for application connection';
    RAISE NOTICE '==============================================';
END $$;