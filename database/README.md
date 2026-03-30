# LLM Testing Database

PostgreSQL database schema for testing and comparing different LLM models and their versions.

## Features

- **Model Management**: Track different LLM models, their versions, and quantizations
- **Test Cases**: Define reusable test scenarios with categories (coding, reasoning, creative, etc.)
- **Test Runs**: Record each test execution with parameters (temperature, tokens, etc.)
- **Results & Scoring**: Store outputs and multi-dimensional scores (accuracy, relevance, coherence, creativity)
- **Performance Views**: Pre-built views for easy analysis and comparison
- **Sample Data**: Includes popular Ollama models (Llama 3.1, DeepSeek Coder, Mistral, etc.)

## Database Schema

### Core Tables

1. **llm_models** - Base model information
   - name, provider, parameters_size, context_window
   
2. **model_versions** - Different versions and quantizations
   - version, quantization, file_size_gb, performance_score
   
3. **test_cases** - Reusable test scenarios
   - name, category, prompt, expected_output, difficulty_level
   
4. **test_runs** - Individual test executions
   - model_version, test_case, parameters (temp, tokens, etc.), execution_time
   
5. **test_results** - Outputs and evaluation scores
   - model_output, scores (accuracy, relevance, coherence, creativity), passed/failed

### Views

- **model_performance_summary** - Aggregate performance metrics per model
- **test_case_performance** - How well different test cases perform across models
- **recent_test_results** - Latest 100 test results

## Setup

### 1. Install PostgreSQL

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download from https://www.postgresql.org/download/windows/

### 2. Install Python Dependencies

```bash
pip install psycopg2-binary
```

Or add to your requirements.txt:
```
psycopg2-binary==2.9.9
```

### 3. Configure Database Connection

Edit `setup_test_db.py` and update the DB_CONFIG:

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'your_postgres_user',
    'password': 'your_postgres_password',
    'database': 'llm_testing'
}
```

### 4. Initialize Database

```bash
cd database
python setup_test_db.py init
```

This will:
- Create the `llm_testing` database
- Create all tables and indexes
- Insert sample models (Llama 3.1, DeepSeek Coder, Mistral, etc.)
- Insert sample test cases
- Create performance views

## Usage

### List Available Models

```bash
python setup_test_db.py models
```

Output:
```
Model                     Provider        Size       Version         Quantization   
llama3.1                  Ollama          8B         latest          Q4_K_M          ⭐
deepseek-coder-v2         Ollama          16B        latest          Q4_K_M          ⭐
mistral                   Ollama          7B         latest          Q4_0            ⭐
```

### List Test Cases

```bash
python setup_test_db.py tests
```

Output:
```
Name                           Category        Difficulty   Tags
Basic Math                     reasoning       easy         math, reasoning
Code Generation - Fibonacci    coding          medium       python, algorithms, dp
Creative Story                 creative        medium       creative, storytelling
```

### View Performance Summary

```bash
python setup_test_db.py summary
```

### Programmatic Usage

```python
from database.setup_test_db import add_test_run, get_model_performance

# Record a test result
add_test_run(
    model_name='llama3.1',
    version='latest',
    test_case_name='Basic Math',
    output='15 * 24 = 360, plus 37 = 397',
    execution_time_ms=1250,
    scores={
        'accuracy': 100,
        'relevance': 95,
        'coherence': 98,
        'creativity': 70
    },
    passed=True
)

# Get performance data
performance = get_model_performance('llama3.1')
for result in performance:
    print(f"{result['version']}: {result['avg_overall_score']:.2f}")
```

## Integration with Your App

### Connect to Database from FastAPI

Add to your `backend/main.py`:

```python
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection pool
def get_test_db():
    conn = psycopg2.connect(
        host='localhost',
        database='llm_testing',
        user='postgres',
        password='postgres'
    )
    return conn

@app.get("/api/llm-models")
async def get_llm_models():
    conn = get_test_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT lm.*, mv.version, mv.quantization 
        FROM llm_models lm
        JOIN model_versions mv ON lm.id = mv.model_id
        WHERE lm.is_active = true
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

@app.post("/api/test-results")
async def save_test_result(data: dict):
    from database.setup_test_db import add_test_run
    success = add_test_run(
        model_name=data['model_name'],
        version=data['version'],
        test_case_name=data['test_case'],
        output=data['output'],
        execution_time_ms=data['execution_time'],
        scores=data.get('scores', {}),
        passed=data.get('passed', True)
    )
    return {"success": success}
```

## Sample Queries

### Compare Models on Specific Test Category

```sql
SELECT 
    lm.name,
    mv.version,
    tc.category,
    AVG(tres.overall_score) as avg_score,
    AVG(tr.execution_time_ms) as avg_time
FROM llm_models lm
JOIN model_versions mv ON lm.id = mv.model_id
JOIN test_runs tr ON mv.id = tr.model_version_id
JOIN test_cases tc ON tr.test_case_id = tc.id
JOIN test_results tres ON tr.id = tres.test_run_id
WHERE tc.category = 'coding'
GROUP BY lm.id, mv.id, tc.category
ORDER BY avg_score DESC;
```

### Find Best Model for Each Category

```sql
WITH ranked_models AS (
    SELECT 
        tc.category,
        lm.name,
        mv.version,
        AVG(tres.overall_score) as avg_score,
        ROW_NUMBER() OVER (PARTITION BY tc.category ORDER BY AVG(tres.overall_score) DESC) as rank
    FROM test_cases tc
    JOIN test_runs tr ON tc.id = tr.test_case_id
    JOIN model_versions mv ON tr.model_version_id = mv.id
    JOIN llm_models lm ON mv.model_id = lm.id
    JOIN test_results tres ON tr.id = tres.test_run_id
    GROUP BY tc.category, lm.name, mv.version
)
SELECT category, name, version, avg_score
FROM ranked_models
WHERE rank = 1;
```

### Track Model Improvement Over Time

```sql
SELECT 
    DATE(tr.run_date) as test_date,
    lm.name,
    AVG(tres.overall_score) as daily_avg_score
FROM test_runs tr
JOIN model_versions mv ON tr.model_version_id = mv.id
JOIN llm_models lm ON mv.model_id = lm.id
JOIN test_results tres ON tr.id = tres.test_run_id
WHERE lm.name = 'llama3.1'
GROUP BY DATE(tr.run_date), lm.name
ORDER BY test_date;
```

## Database Backup

```bash
# Backup
pg_dump -U postgres llm_testing > llm_testing_backup.sql

# Restore
psql -U postgres llm_testing < llm_testing_backup.sql
```

## Customization

### Add New Model

```sql
INSERT INTO llm_models (name, provider, category_id, parameters_size, context_window)
VALUES ('gpt-4', 'OpenAI', 1, '1.76T', 128000);

INSERT INTO model_versions (model_id, version, is_default)
VALUES ((SELECT id FROM llm_models WHERE name = 'gpt-4'), 'gpt-4-turbo', true);
```

### Add New Test Case

```sql
INSERT INTO test_cases (name, category, prompt, difficulty_level, tags)
VALUES (
    'API Documentation',
    'coding',
    'Write comprehensive API documentation for a REST endpoint that creates user accounts.',
    'medium',
    ARRAY['documentation', 'api', 'rest']
);
```

## Troubleshooting

### Connection Refused

Check if PostgreSQL is running:
```bash
# macOS
brew services list

# Linux
sudo systemctl status postgresql
```

### Authentication Failed

Reset PostgreSQL password:
```bash
sudo -u postgres psql
ALTER USER postgres PASSWORD 'newpassword';
```

### Database Already Exists

Drop and recreate:
```bash
dropdb -U postgres llm_testing
python setup_test_db.py init
```

## License

MIT
