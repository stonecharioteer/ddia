# CLI Architecture Documentation

This document describes the architecture of the database demonstration CLI tool and provides guidelines for extending it.

## Overview

The CLI is built using Python's `click` library and provides a unified interface for demonstrating database operations across PostgreSQL, MongoDB, and Neo4j. The tool is designed to be modular and easily extensible.

## Project Structure

```
.
├── script.py                    # Main CLI entry point
├── architecture.md              # This documentation
├── sql/                        # SQL files for PostgreSQL operations
│   ├── schema.sql              # Database schema definition
│   ├── summary.sql             # Skill count summary query
│   ├── followers.sql           # Friends-of-friends analysis
│   ├── follower_with_ge_x_followers.sql
│   └── query.sql               # General queries
├── postgres.py                 # PostgreSQL operations and utilities
├── mongodb.py                  # MongoDB operations  
├── neo4j_social.py            # Neo4j operations
└── resume/                    # Legacy directory (may contain other files)
```

## CLI Structure

The CLI uses click's command group pattern to organize operations by database type:

```
script.py [DATABASE] [COMMAND] [OPTIONS]
```

### Command Groups

#### PostgreSQL (`script.py postgres`)
- `create-schemas` - Create database tables from schema.sql
- `populate-data [--users N]` - Populate with fake data (default 5000 users)
- `summary` - Run skill count summary from summary.sql  
- `followers [--user-id N]` - Run follower analysis for specific user

#### MongoDB (`script.py mongo`)
- `populate-data [--resumes N]` - Generate fake resumes (default 50)
- `filter` - Run various filtering queries
- `summary` - Run aggregation pipeline for skill counts
- `summary-mapreduce` - Run legacy MapReduce skill summary

#### Neo4j (`script.py neo4j`)
- `create-user [--name NAME]` - Create a user node (default: Alice)

## Key Components

### 1. Main CLI Module (`script.py`)

The main CLI module defines the command groups and routes commands to the appropriate database modules. Each command includes:

- Error handling with try/catch blocks
- User-friendly success/error messages with ✓/✗ indicators
- Consistent parameter passing to underlying functions

### 2. Database Modules

Each database has its own module with specific operations:

- **`postgres.py`**: Contains PostgreSQL operations and the `run_sql_file()` utility
- **`mongodb.py`**: Contains MongoDB operations using pymongo
- **`neo4j_social.py`**: Contains Neo4j operations using the neo4j driver

### 3. SQL Files (`sql/` directory)

PostgreSQL queries are stored as separate SQL files for better organization:

- Files support parameter substitution using `$parameter_name` syntax
- The `run_sql_file()` function handles parameter replacement and execution
- SELECT queries automatically display results; other queries just confirm execution

## Adding New Commands

### Adding a PostgreSQL Command

1. **Add the function to `postgres.py`**:
   ```python
   def my_new_operation():
       """Description of what this does"""
       # Your implementation here
       print("Operation completed")
   ```

2. **Add the CLI command to `script.py`**:
   ```python
   @postgres.command('my-command')
   @click.option('--param', default=10, help='Description of parameter')
   def postgres_my_command(param):
       """Description for CLI help."""
       try:
           my_new_operation(param)
           click.echo("✓ My operation completed successfully")
       except Exception as e:
           click.echo(f"✗ Error: {e}", err=True)
           raise click.Abort()
   ```

3. **Add import to `script.py`**:
   ```python
   from postgres import create_schemas, populate_initial_skills, load_data, add_followers, run_sql_file, my_new_operation
   ```

### Adding a New Database

1. **Create a new module** (e.g., `redis_ops.py`) with your database operations

2. **Add a new command group in `script.py`**:
   ```python
   @cli.group()
   def redis():
       """Redis operations."""
       pass

   @redis.command('my-command')
   def redis_my_command():
       """Redis command description."""
       # Implementation here
   ```

3. **Add imports** at the top of `script.py`

### Adding SQL Files

1. **Create your SQL file** in the `sql/` directory
2. **Use parameter substitution** if needed: `WHERE user_id = $user_id`
3. **Call via CLI**:
   ```python
   @postgres.command('my-query')
   @click.option('--user-id', default=1)
   def postgres_my_query(user_id):
       try:
           run_sql_file('my_query.sql', user_id=user_id)
           click.echo("✓ Query completed")
       except Exception as e:
           click.echo(f"✗ Error: {e}", err=True)
           raise click.Abort()
   ```

## Design Patterns

### Error Handling
All CLI commands follow this pattern:
```python
try:
    # Call the actual operation
    result = some_operation()
    click.echo("✓ Success message")
except Exception as e:
    click.echo(f"✗ Error: {e}", err=True)
    raise click.Abort()
```

### Parameter Passing
- Use click options for CLI parameters
- Pass parameters directly to underlying functions
- For SQL files, pass as keyword arguments to `run_sql_file()`

### Import Organization
- Keep database-specific operations in their respective modules
- Import only what's needed in the main CLI module
- Avoid circular imports by keeping the CLI as the top-level orchestrator

## Usage Examples

```bash
# PostgreSQL operations
python script.py postgres create-schemas
python script.py postgres populate-data --users 1000
python script.py postgres summary
python script.py postgres followers --user-id 5

# MongoDB operations  
python script.py mongo populate-data --resumes 100
python script.py mongo filter
python script.py mongo summary

# Neo4j operations
python script.py neo4j create-user --name "Bob"
```

## Best Practices

1. **Keep database logic in database modules**: Don't put database-specific code in `script.py`
2. **Use descriptive command names**: Prefer `create-schemas` over `create`
3. **Provide helpful error messages**: Users should understand what went wrong
4. **Include parameter validation**: Validate inputs before calling database operations
5. **Document everything**: Add docstrings to all functions and commands
6. **Test with small datasets first**: Provide reasonable defaults for testing

## Future Extensions

The architecture supports easy addition of:
- New database types (Redis, Elasticsearch, etc.)
- Batch operations across multiple databases  
- Configuration files for connection strings
- Output formatting options (JSON, CSV, etc.)
- Logging and verbose output modes
- Data validation and schema checking

This modular design ensures the tool can grow with your demonstration needs while maintaining clean separation of concerns.