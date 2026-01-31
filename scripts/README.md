# Database Reset Scripts

This directory contains scripts for managing your Neon PostgreSQL database.

## reset-auth-data.py

**Purpose:** Clear all authentication and user-related data while preserving the database schema.

**Use When:**
- Authentication flow is broken (signup succeeds but login fails)
- Session expires immediately after login
- Dashboard redirects back to sign-in page
- "Failed to fetch" errors on the frontend
- Need to start fresh with a clean database

### What Gets Deleted

The script clears data from these tables in the correct order (respecting foreign key constraints):

**Better Auth Tables (camelCase):**
- `account` - User OAuth accounts
- `session` - Active user sessions
- `verification` - Email/phone verification tokens
- `jwks` - JSON Web Key Sets
- `user` - Better Auth users

**Backend Tables (snake_case):**
- `tasks` - User tasks
- `users` - Backend user records

**Sequences Reset:**
- `tasks_id_seq` - Reset to 1

### What Is Preserved

- Database schema (all table structures)
- Indexes and constraints
- Functions and triggers
- The `playing_with_neon` table (demo data)

### Usage

#### Method 1: Run the Python Script (Recommended)

```bash
# From the project root directory
cd /mnt/d/Hackathon_Projects/hackathon_project2/The-Evolution-of-Todo-Application

# Run the reset script
python scripts/reset-auth-data.py
```

The script will:
1. Read the DATABASE_URL from `backend/.env`
2. Show current row counts
3. Delete all data in the correct order
4. Reset sequences
5. Verify all tables are empty
6. Show next steps

#### Method 2: Run the SQL Script Directly

If you have `psql` installed:

```bash
# Export your DATABASE_URL
export DATABASE_URL="postgresql://neondb_owner:npg_xxx@ep-xxx.neon.tech/neondb?sslmode=require"

# Run the SQL script
psql "$DATABASE_URL" -f scripts/reset-auth-data.sql
```

Or using the Neon CLI:

```bash
neon connection-string <branch-name> | xargs -I {} psql {} -f scripts/reset-auth-data.sql
```

### After Running the Reset

1. **Restart your backend server:**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Restart your frontend dev server:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test the authentication flow:**
   - Navigate to http://localhost:3000/sign-up
   - Create a new account
   - Verify you're redirected to the dashboard
   - Check that your session persists
   - Try logging out and back in

### Troubleshooting

**If you get "Network is unreachable" errors:**
- This is usually an IPv6 connectivity issue in WSL2
- Run the script from Windows PowerShell instead:
  ```powershell
  python scripts\reset-auth-data.py
  ```
- Or use WSL1 if available

**If you get "connection refused" errors:**
- Check that your Neon database is running
- Verify the DATABASE_URL in `backend/.env` is correct
- Test the connection: `psql "$DATABASE_URL" -c "SELECT 1"`

**If some tables still have data after reset:**
- There may be foreign key constraint issues
- Check the error message for details
- You may need to manually delete data in a specific order

### Safety Features

- Uses transactions (will rollback on error)
- Shows before/after row counts
- Verifies all tables are empty before reporting success
- Never drops tables or modifies schema
- Preserves non-auth related data (like `playing_with_neon`)

### Database Schema Information

**Foreign Key Relationships:**
- `account.userId` → `user.id`
- `session.userId` → `user.id`
- `tasks.user_id` → `users.id`

**Deletion Order (Child → Parent):**
1. `account`, `session`, `verification`, `jwks` (child tables)
2. `user` (parent for Better Auth)
3. `tasks` (child table)
4. `users` (parent for backend)
