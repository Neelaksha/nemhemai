-- LLM Testing Database Schema
-- PostgreSQL database for tracking LLM models, versions, and test results

-- Drop existing tables if they exist
DROP TABLE IF EXISTS test_results CASCADE;
DROP TABLE IF EXISTS test_runs CASCADE;
DROP TABLE IF EXISTS test_cases CASCADE;
DROP TABLE IF EXISTS model_versions CASCADE;
DROP TABLE IF EXISTS llm_models CASCADE;
DROP TABLE IF EXISTS model_categories CASCADE;

-- Model Categories (e.g., Chat, Code, Analysis, Embedding)
CREATE TABLE model_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LLM Models (Base model information)
CREATE TABLE llm_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    provider VARCHAR(100) NOT NULL, -- e.g., Ollama, OpenAI, Anthropic
    category_id INTEGER REFERENCES model_categories(id),
    description TEXT,
    parameters_size VARCHAR(50), -- e.g., "7B", "13B", "70B"
    context_window INTEGER, -- Token context window size
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, provider)
);

-- Model Versions (Track different versions of the same model)
CREATE TABLE model_versions (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES llm_models(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    release_date DATE,
    quantization VARCHAR(50), -- e.g., "Q4_K_M", "Q8_0", "fp16"
    file_size_gb DECIMAL(10, 2),
    notes TEXT,
    performance_score DECIMAL(5, 2), -- Average performance score
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_id, version)
);

-- Test Cases (Define test scenarios)
CREATE TABLE test_cases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100), -- e.g., "reasoning", "coding", "math", "creative"
    prompt TEXT NOT NULL,
    expected_output TEXT,
    evaluation_criteria JSONB, -- Store criteria as JSON
    difficulty_level VARCHAR(20), -- easy, medium, hard
    tags TEXT[], -- Array of tags for categorization
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Test Runs (Track individual test executions)
CREATE TABLE test_runs (
    id SERIAL PRIMARY KEY,
    model_version_id INTEGER REFERENCES model_versions(id) ON DELETE CASCADE,
    test_case_id INTEGER REFERENCES test_cases(id) ON DELETE CASCADE,
    run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temperature DECIMAL(3, 2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 1000,
    top_p DECIMAL(3, 2) DEFAULT 0.9,
    top_k INTEGER DEFAULT 40,
    other_params JSONB, -- Store additional parameters
    execution_time_ms INTEGER, -- Response time in milliseconds
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    error_message TEXT
);

-- Test Results (Store outputs and evaluations)
CREATE TABLE test_results (
    id SERIAL PRIMARY KEY,
    test_run_id INTEGER REFERENCES test_runs(id) ON DELETE CASCADE,
    model_output TEXT,
    token_count INTEGER,
    accuracy_score DECIMAL(5, 2), -- 0-100 scale
    relevance_score DECIMAL(5, 2),
    coherence_score DECIMAL(5, 2),
    creativity_score DECIMAL(5, 2),
    overall_score DECIMAL(5, 2), -- Average or weighted score
    human_rating INTEGER CHECK (human_rating >= 1 AND human_rating <= 5),
    evaluator_notes TEXT,
    passed BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX idx_llm_models_provider ON llm_models(provider);
CREATE INDEX idx_llm_models_category ON llm_models(category_id);
CREATE INDEX idx_model_versions_model ON model_versions(model_id);
CREATE INDEX idx_test_runs_model_version ON test_runs(model_version_id);
CREATE INDEX idx_test_runs_test_case ON test_runs(test_case_id);
CREATE INDEX idx_test_runs_date ON test_runs(run_date);
CREATE INDEX idx_test_results_run ON test_results(test_run_id);
CREATE INDEX idx_test_cases_category ON test_cases(category);

-- Create views for easy querying

-- View: Model Performance Summary
CREATE VIEW model_performance_summary AS
SELECT 
    lm.name AS model_name,
    lm.provider,
    mv.version,
    mv.quantization,
    COUNT(DISTINCT tr.id) AS total_tests,
    AVG(tres.overall_score) AS avg_overall_score,
    AVG(tres.accuracy_score) AS avg_accuracy,
    AVG(tres.relevance_score) AS avg_relevance,
    AVG(tres.coherence_score) AS avg_coherence,
    AVG(tr.execution_time_ms) AS avg_response_time_ms,
    SUM(CASE WHEN tres.passed THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(tres.id), 0) * 100 AS pass_rate
FROM llm_models lm
JOIN model_versions mv ON lm.id = mv.model_id
JOIN test_runs tr ON mv.id = tr.model_version_id
LEFT JOIN test_results tres ON tr.id = tres.test_run_id
WHERE tr.status = 'completed'
GROUP BY lm.id, lm.name, lm.provider, mv.id, mv.version, mv.quantization
ORDER BY avg_overall_score DESC;

-- View: Test Case Performance
CREATE VIEW test_case_performance AS
SELECT 
    tc.name AS test_case_name,
    tc.category,
    tc.difficulty_level,
    COUNT(DISTINCT tr.id) AS times_tested,
    AVG(tres.overall_score) AS avg_score,
    AVG(tr.execution_time_ms) AS avg_time_ms,
    SUM(CASE WHEN tres.passed THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(tres.id), 0) * 100 AS pass_rate
FROM test_cases tc
JOIN test_runs tr ON tc.id = tr.test_case_id
LEFT JOIN test_results tres ON tr.id = tres.test_run_id
WHERE tr.status = 'completed'
GROUP BY tc.id, tc.name, tc.category, tc.difficulty_level
ORDER BY avg_score DESC;

-- View: Recent Test Results
CREATE VIEW recent_test_results AS
SELECT 
    tr.id AS test_run_id,
    lm.name AS model_name,
    mv.version,
    tc.name AS test_case_name,
    tc.category,
    tr.run_date,
    tr.execution_time_ms,
    tres.overall_score,
    tres.passed,
    tr.status
FROM test_runs tr
JOIN model_versions mv ON tr.model_version_id = mv.id
JOIN llm_models lm ON mv.model_id = lm.id
JOIN test_cases tc ON tr.test_case_id = tc.id
LEFT JOIN test_results tres ON tr.id = tres.test_run_id
ORDER BY tr.run_date DESC
LIMIT 100;

-- Insert sample data for model categories
INSERT INTO model_categories (name, description) VALUES
('Chat', 'General conversation and question-answering models'),
('Code', 'Programming and code generation models'),
('Analysis', 'Data analysis and reasoning models'),
('Creative', 'Creative writing and content generation'),
('Embedding', 'Text embedding and semantic search models');

-- Insert sample LLM models
INSERT INTO llm_models (name, provider, category_id, description, parameters_size, context_window) VALUES
('llama3.1', 'Ollama', 1, 'Meta Llama 3.1 - Advanced chat model', '8B', 128000),
('deepseek-coder-v2', 'Ollama', 2, 'DeepSeek Coder V2 - Code generation specialist', '16B', 16000),
('mistral', 'Ollama', 1, 'Mistral - Efficient general purpose model', '7B', 8000),
('gemma2', 'Ollama', 1, 'Google Gemma 2 - Lightweight chat model', '9B', 8192),
('codellama', 'Ollama', 2, 'Code Llama - Meta code specialist', '7B', 16000),
('qwen2.5', 'Ollama', 1, 'Qwen 2.5 - Alibaba advanced model', '7B', 32000),
('phi3', 'Ollama', 1, 'Microsoft Phi-3 - Small efficient model', '3.8B', 4000);

-- Insert sample model versions
INSERT INTO model_versions (model_id, version, quantization, file_size_gb, is_default) VALUES
(1, 'latest', 'Q4_K_M', 4.7, true),
(1, '8b-q8', 'Q8_0', 8.5, false),
(2, 'latest', 'Q4_K_M', 8.9, true),
(3, 'latest', 'Q4_0', 4.1, true),
(3, '7b-instruct-q8', 'Q8_0', 7.7, false),
(4, 'latest', 'Q4_K_M', 5.4, true),
(5, 'latest', 'Q4_K_M', 3.8, true),
(6, 'latest', 'Q4_K_M', 4.5, true),
(7, 'latest', 'Q4_K_M', 2.3, true);

-- Insert sample test cases
INSERT INTO test_cases (name, category, prompt, difficulty_level, tags) VALUES
('Basic Math', 'reasoning', 'What is 15 * 24 + 37? Explain your calculation.', 'easy', ARRAY['math', 'reasoning']),
('Code Generation - Fibonacci', 'coding', 'Write a Python function to calculate the nth Fibonacci number using dynamic programming.', 'medium', ARRAY['python', 'algorithms', 'dp']),
('Creative Story', 'creative', 'Write a short story (3 paragraphs) about a robot learning to paint.', 'medium', ARRAY['creative', 'storytelling']),
('Data Analysis', 'reasoning', 'Given a dataset with columns: date, sales, region. How would you analyze sales trends over time?', 'hard', ARRAY['analysis', 'data']),
('Code Debug', 'coding', 'Find and fix the bug in this code: def sum_list(lst): total = 0; for i in range(len(lst)+1): total += lst[i]; return total', 'medium', ARRAY['debugging', 'python']),
('Logical Reasoning', 'reasoning', 'If all roses are flowers and some flowers fade quickly, can we conclude that some roses fade quickly?', 'hard', ARRAY['logic', 'reasoning']),
('SQL Query', 'coding', 'Write a SQL query to find the top 5 customers by total purchase amount in 2024.', 'easy', ARRAY['sql', 'databases']),
('Explanation', 'reasoning', 'Explain the difference between supervised and unsupervised machine learning in simple terms.', 'easy', ARRAY['ml', 'explanation']);

COMMENT ON TABLE llm_models IS 'Stores information about different LLM models';
COMMENT ON TABLE model_versions IS 'Tracks different versions and quantizations of models';
COMMENT ON TABLE test_cases IS 'Defines test scenarios for evaluating models';
COMMENT ON TABLE test_runs IS 'Records individual test executions with parameters';
COMMENT ON TABLE test_results IS 'Stores test outputs and evaluation scores';
