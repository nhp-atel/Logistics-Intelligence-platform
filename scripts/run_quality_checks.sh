#!/bin/bash
# Run data quality checks

set -e

echo "=== Running Data Quality Checks ==="
echo

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-""}
GE_DIR="great_expectations"

# Check if Great Expectations is installed
if ! python -c "import great_expectations" 2>/dev/null; then
    echo "Installing Great Expectations..."
    pip install great-expectations
fi

# Run Great Expectations checkpoint
echo "Running Great Expectations validation..."
cd $GE_DIR

# Check if data context exists
if [ ! -f "great_expectations.yml" ]; then
    echo "ERROR: Great Expectations not initialized"
    echo "Run: great_expectations init"
    exit 1
fi

# Run the checkpoint
great_expectations checkpoint run data_quality_checkpoint

echo
echo "=== Data Quality Checks Complete ==="
echo "View results in: $GE_DIR/uncommitted/data_docs/local_site/index.html"
