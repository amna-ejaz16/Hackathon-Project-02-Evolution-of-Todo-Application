---
name: database-skill
description: Design and manage databases including schema design, table creation, and migrations for scalable applications.
---

# Database Skill – Schema, Tables & Migrations

## Instructions

1. **Schema Design**
   - Identify core entities and relationships
   - Normalize data where appropriate
   - Define primary keys and foreign keys
   - Plan for scalability and future changes

2. **Table Creation**
   - Create clear and consistent table structures
   - Use appropriate data types
   - Apply constraints (NOT NULL, UNIQUE, FK)
   - Index frequently queried columns

3. **Migrations**
   - Use versioned migration files
   - Support up and down migrations
   - Avoid destructive changes without backups
   - Keep migrations atomic and reversible

4. **Data Integrity**
   - Enforce referential integrity
   - Use transactions for multi-step operations
   - Handle cascading updates and deletes safely

5. **Environment Awareness**
   - Separate development, staging, and production schemas
   - Use environment-based configuration
   - Support local and cloud databases (Postgres, MySQL, SQLite)

## Best Practices

- Use snake_case for table and column names
- Prefer UUIDs or auto-increment IDs consistently
- Avoid storing derived or duplicate data
- Keep schema changes backward-compatible
- Document schema decisions clearly

## Example Schema (SQL)

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
