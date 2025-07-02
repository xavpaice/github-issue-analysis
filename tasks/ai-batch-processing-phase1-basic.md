# Task: AI Batch Processing - Phase 1: Basic OpenAI Batch Processing

**Status:** ready  
**Priority:** high  
**Estimated Time:** 3-4 hours  
**Dependencies:** None - works with existing JSON storage

## Description
Implement basic OpenAI Batch API integration for cost-effective AI processing. Works with existing JSON issue files without requiring DuckDB.

## Value Delivered
- **50% cost reduction** - OpenAI charges 50% less for batch API vs real-time API
- **High-volume processing** - Handle 100+ issues efficiently in one batch job
- **Asynchronous workflow** - Submit jobs and check back later (up to 24 hours)

## Files to Create
- `github_issue_analysis/ai/batch/batch_manager.py` - Core batch job management
- `github_issue_analysis/ai/batch/openai_provider.py` - OpenAI Batch API client
- `github_issue_analysis/ai/batch/models.py` - Batch job models
- `github_issue_analysis/cli/batch.py` - Batch processing CLI
- `tests/test_ai/test_batch.py` - Batch functionality tests

## Files to Modify
- `github_issue_analysis/cli/main.py` - Add batch commands
- `pyproject.toml` - Add any new dependencies

## New Operations
```bash
# Submit batch job from issue files
uv run github-analysis batch submit product-labeling --files "data/issues/org_repo_*.json"

# Check batch job status
uv run github-analysis batch status <job-id>

# Collect completed batch results
uv run github-analysis batch collect <job-id>

# List all batch jobs
uv run github-analysis batch list
```

## New Functionality
- Process multiple issues at once instead of one-by-one
- 50% cheaper per API call (OpenAI's batch pricing)
- Submit job, go away, come back later for results
- Convert existing issue JSON files to OpenAI JSONL format
- Handle batch job lifecycle (submit → monitor → collect)

## Implementation Details

### Batch Manager
```python
class BatchManager:
    """Manages AI batch processing jobs."""
    
    async def create_batch_job(self, 
                              processor_type: str,
                              issue_files: List[Path],
                              model_config: AIModelConfig) -> BatchJob:
        """Create batch job from issue files."""
        
    async def check_job_status(self, job_id: str) -> BatchJobStatus:
        """Check status of batch job."""
        
    async def collect_results(self, job_id: str) -> Dict[str, Any]:
        """Download and process batch results."""
```

### OpenAI Provider
```python
class OpenAIBatchProvider:
    """OpenAI Batch API implementation."""
    
    def create_jsonl_file(self, issues: List[Dict], processor_config: Dict) -> Path:
        """Convert issues to OpenAI JSONL format with custom_id for tracking."""
        
    async def submit_batch(self, jsonl_file: Path) -> str:
        """Submit batch job to OpenAI."""
        
    async def get_batch_status(self, batch_id: str) -> Dict:
        """Get batch job status from OpenAI."""
        
    async def download_results(self, batch_id: str) -> List[Dict]:
        """Download completed batch results."""
```

### JSONL Format
```jsonl
{"custom_id": "org_repo_issue_123", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-4o-mini", "messages": [...]}}
{"custom_id": "org_repo_issue_124", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-4o-mini", "messages": [...]}}
```

## Validation Steps

### **Setup and Testing**
```bash
# 1. Ensure existing data is available
uv run github-analysis status

# 2. Test batch submission
uv run github-analysis batch submit product-labeling --files "data/issues/test_org_*.json"

# 3. Check job status
uv run github-analysis batch status <job-id>

# 4. Collect results when ready
uv run github-analysis batch collect <job-id>

# 5. Verify results are in correct format
ls data/results/*_product-labeling.json
```

### **Error Handling**
```bash
# 6. Test with invalid files
uv run github-analysis batch submit product-labeling --files "nonexistent/*.json"

# 7. Test with malformed JSON
# Create malformed test file and verify graceful handling
```

## Success Criteria
- [ ] Create JSONL files from existing issue JSON files
- [ ] Submit batch jobs to OpenAI Batch API  
- [ ] Poll job status and handle completion
- [ ] Download and parse batch results
- [ ] Save results in existing JSON format (`data/results/`)
- [ ] CLI commands for end-to-end batch workflow
- [ ] Error handling for failed batch items
- [ ] Cost tracking and comparison with real-time processing

## Agent Notes
[Document implementation approach, API integration challenges, and cost optimization strategies]