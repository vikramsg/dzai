# GitHub CLI for LLM-Based Code Review: Complete Guide

## Executive Summary

To enable LLM-based code review with the GitHub CLI (`gh`), you need to combine the `gh` CLI's built-in commands with the GitHub REST API (via `gh api`) for inline comments. The native `gh pr review` command only supports PR-level comments, but inline comments on specific lines require using the GitHub REST API through `gh api`.

## Required Commands

### 1. Viewing Pull Request Information

**Get PR details and diff:**
```bash
# View PR information
gh pr view <PR_NUMBER> --json title,body,headRefOid,files

# View the diff
gh pr diff <PR_NUMBER>

# Get PR in JSON format with specific fields
gh pr view <PR_NUMBER> --json number,title,body,files,reviews
```

[Official Documentation: gh pr view](https://cli.github.com/manual/gh_pr)

### 2. Adding Comments

#### A. General PR Comments (Simple)

The `gh pr comment` command adds a comment to a GitHub pull request:

```bash
# Add a general comment to the PR
gh pr comment <PR_NUMBER> -b "Your review comment here"

# Add comment from file
gh pr comment <PR_NUMBER> -F comment.txt
```

[Official Documentation: gh pr comment](https://cli.github.com/manual/gh_pr_comment)

#### B. PR-Level Review (Approve/Request Changes/Comment)

Use `gh pr review` for approval, requesting changes, or leaving review comments:

```bash
# Approve the PR
gh pr review <PR_NUMBER> --approve

# Request changes
gh pr review <PR_NUMBER> --request-changes -b "Please address these issues"

# Leave a comment review
gh pr review <PR_NUMBER> --comment -b "Looks good overall"
```

[Official Documentation: gh pr review](https://cli.github.com/manual/gh_pr_review)

#### C. Inline Comments on Specific Lines (Advanced - Using gh api)

For inline comments pinned to file and line numbers, you must use the GitHub REST API via `gh api`:

```bash
# Create an inline comment on a specific line
gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/OWNER/REPO/pulls/PULL_NUMBER/comments \
  -f body='Great stuff!' \
  -f commit_id='<COMMIT_SHA>' \
  -f path='src/file.py' \
  -F line=42 \
  -f side='RIGHT'
```

**For multi-line comments:**
```bash
gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/OWNER/REPO/pulls/PULL_NUMBER/comments \
  -f body='This section needs refactoring' \
  -f commit_id='<COMMIT_SHA>' \
  -f path='src/file.py' \
  -F start_line=10 \
  -f start_side='RIGHT' \
  -F line=15 \
  -f side='RIGHT'
```

**Important Parameters:**
- `commit_id`: The SHA of the commit (typically the HEAD commit of the PR)
- `path`: Relative file path in the repository
- `line`: The line number in the diff (for single-line comments) or end line (for multi-line)
- `side`: `RIGHT` for additions, `LEFT` for deletions
- `start_line` and `start_side`: Required for multi-line comments

[Official Documentation: REST API Pull Request Review Comments](https://docs.github.com/en/rest/pulls/comments)

### 3. Creating Reviews with Multiple Inline Comments

You can create a review with multiple inline comments in a single API call using the reviews endpoint:

```bash
gh api \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/OWNER/REPO/pulls/PULL_NUMBER/reviews \
  -f commit_id="<COMMIT_SHA>" \
  -f body="Overall review summary" \
  -f event="COMMENT" \
  -f comments[][path]="file.md" \
  -f comments[][line]=6 \
  -f comments[][side]="RIGHT" \
  -f comments[][body]="Please add more information here."
```

**Event types:**
- `APPROVE`: Approve the PR
- `REQUEST_CHANGES`: Request changes
- `COMMENT`: Submit review without approval status

[Official Documentation: REST API Pull Request Reviews](https://docs.github.com/en/rest/pulls/reviews)

## Required Permissions

### Authentication Setup

The minimum required scopes for the token are: `repo`, `read:org`, and `gist`:

```bash
# Interactive authentication
gh auth login

# Authenticate with token from file
gh auth login --with-token < token.txt

# Set token via environment variable (recommended for automation)
export GH_TOKEN="your_token_here"
```

[Official Documentation: gh auth login](https://cli.github.com/manual/gh_auth_login)

### Token Permissions

#### Classic Personal Access Token (PAT)

For classic tokens, you need:
- **`repo`** - Full control of private repositories (includes PR access)
- **`read:org`** - Read org and team membership
- **`gist`** - (optional, but included in default gh setup)

#### Fine-Grained Personal Access Token (Recommended)

Fine-grained tokens offer over 50 granular permissions with 'no access', 'read', or 'read and write' basis.

**Minimum required permissions for code review:**

**Repository Permissions:**
- **Pull requests**: Read and write (required for creating reviews and comments)
- **Contents**: Read (required to view code and diffs)
- **Metadata**: Read (automatically included)

**Organization Permissions (if reviewing org repos):**
- **Members**: Read (optional, only if you need to request reviews from teams)

**How to create:**
1. Go to Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens
2. Select repository access (specific repositories or all)
3. Set the permissions as listed above
4. Generate token

[Official Documentation: Managing Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

### GitHub Actions Integration

In GitHub Actions, use `GH_TOKEN: ${{ github.token }}` in the environment:

```yaml
- name: Review PR
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    gh pr view ${{ github.event.pull_request.number }}
```

The default `GITHUB_TOKEN` has permissions to comment on PRs in the same repository.

[Official Documentation: GitHub Actions Token Authentication](https://docs.github.com/actions/security-guides/automatic-token-authentication)

## Complete Example Script

Here's a complete bash script demonstrating LLM-based code review:

```bash
#!/bin/bash

# LLM Code Review Script using gh CLI
# Usage: ./review.sh <owner/repo> <PR_NUMBER>

REPO=$1
PR_NUMBER=$2

echo "Reviewing PR #${PR_NUMBER} in ${REPO}"

# 1. Get PR information
PR_INFO=$(gh pr view ${PR_NUMBER} --repo ${REPO} --json headRefOid,files)
COMMIT_SHA=$(echo "$PR_INFO" | jq -r '.headRefOid')

echo "Commit SHA: ${COMMIT_SHA}"

# 2. Get the diff
DIFF=$(gh pr diff ${PR_NUMBER} --repo ${REPO})

# 3. Pass diff to LLM for analysis (example with pseudocode)
# REVIEW_COMMENTS=$(echo "$DIFF" | llm_analyze)

# Example: Create inline comment on specific line
gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/${REPO}/pulls/${PR_NUMBER}/comments \
  -f body="Consider using a constant for this magic number" \
  -f commit_id="${COMMIT_SHA}" \
  -f path="src/main.py" \
  -F line=42 \
  -f side="RIGHT"

# 4. Submit overall review
gh pr review ${PR_NUMBER} --repo ${REPO} \
  --comment -b "LLM Review completed: Found 3 suggestions for improvement"

echo "Review submitted successfully"
```

## GitHub Actions Workflow Example

Here's an example workflow for automated code review using an LLM agent with gh CLI:

```yaml
name: LLM Code Review
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  pull-requests: write
  contents: read

jobs:
  code-review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ github.event.pull_request.head.sha }}

      - name: Get PR diff
        id: diff
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh pr diff ${{ github.event.pull_request.number }} > pr_diff.txt

      - name: Analyze with LLM
        id: analyze
        run: |
          # Call your LLM service here
          # Example: curl to OpenAI/Anthropic/etc with pr_diff.txt
          # Store results in review_comments.json
          echo "[]" > review_comments.json

      - name: Post review comments
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          COMMIT_SHA="${{ github.event.pull_request.head.sha }}"
          REPO="${{ github.repository }}"
          PR_NUMBER="${{ github.event.pull_request.number }}"
          
          # Parse review_comments.json and post each comment
          jq -c '.[]' review_comments.json | while read comment; do
            BODY=$(echo "$comment" | jq -r '.body')
            PATH=$(echo "$comment" | jq -r '.path')
            LINE=$(echo "$comment" | jq -r '.line')
            
            gh api \
              --method POST \
              -H "Accept: application/vnd.github+json" \
              -H "X-GitHub-Api-Version: 2022-11-28" \
              /repos/${REPO}/pulls/${PR_NUMBER}/comments \
              -f body="$BODY" \
              -f commit_id="$COMMIT_SHA" \
              -f path="$PATH" \
              -F line=$LINE \
              -f side="RIGHT"
          done

      - name: Submit review summary
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh pr review ${{ github.event.pull_request.number }} \
            --comment -b "🤖 Automated code review completed"
```

[Reference: Cursor CLI Code Review Example](https://docs.cursor.com/en/cli/cookbook/code-review)

## Common Pitfalls and Solutions

### 1. Inline Comments Not Visible with `gh pr view --comments`

**Problem:** The `gh pr view --comments` command doesn't include inline review comments.

**Solution:** Use `gh api` to fetch review comments:
```bash
gh api /repos/OWNER/REPO/pulls/PULL_NUMBER/comments
```

### 2. Line Numbers in Diff vs. File

**Problem:** Pull request review comments must reference lines in the diff, not lines in the original file.

**Solution:** Line numbers shown in the PR diff may differ from original file numbering due to additions/deletions. Always use line numbers as shown in the PR diff.

### 3. Getting the Correct Commit SHA

**Problem:** Comments must reference a valid commit SHA from the PR.

**Solution:**
```bash
# Get the HEAD commit of the PR
COMMIT_SHA=$(gh pr view <PR_NUMBER> --json headRefOid -q '.headRefOid')
```

### 4. Rate Limiting

**Problem:** Creating comments too quickly may result in secondary rate limiting.

**Solution:** 
- Batch comments into a single review using the `/reviews` endpoint
- Add delays between individual comment API calls
- Use the review submission endpoint which allows multiple comments in one request

### 5. Permission Errors with Fine-Grained Tokens

**Problem:** Fine-grained tokens without "Organization: Member" permission cannot validate team reviewers.

**Solution:** If requesting reviews from teams, add "Organization: Members" read permission to your token.

### 6. Fetching Review Comments with Line Details

**Problem:** `gh pr view --json reviews` only fetches the review body and state, but not the line comments themselves. You must use `gh api` to manually fetch review comments.

**Solution:**
```bash
# Fetch all review comments for a PR
gh api /repos/OWNER/REPO/pulls/PULL_NUMBER/comments | jq '.[] | {path, line, body}'
```

## Best Practices

### 1. Use Reviews for Batching Comments

Instead of creating individual comments, create a review with multiple comments:

```bash
# More efficient - single API call
gh api -X POST \
  /repos/OWNER/REPO/pulls/PULL_NUMBER/reviews \
  -f event="COMMENT" \
  -f body="Review summary" \
  -f comments='[
    {"path":"file1.py","line":10,"body":"Comment 1","side":"RIGHT"},
    {"path":"file2.py","line":20,"body":"Comment 2","side":"RIGHT"}
  ]'
```

### 2. Environment Variable for Authentication

Setting `GH_TOKEN` as an environment variable is most suitable for headless use of gh in automation:

```bash
export GH_TOKEN="ghp_your_token_here"
# or for fine-grained tokens (recommended)
export GH_TOKEN="github_pat_your_token_here"
```

### 3. JSON Output for Parsing

When gh output is piped, it formats output in a machine-readable format with tab-delimited fields and no color escape sequences:

```bash
gh pr list --json number,title,author | jq '.[] | select(.author.login == "bot")'
```

### 4. Limit Comment Volume

Limit the number of comments to avoid overwhelming developers. Best practice: max 10-15 inline comments per review focusing on high-priority issues.

### 5. Check for Existing Comments

Before posting, check if similar feedback already exists to avoid duplicates:

```bash
gh api /repos/OWNER/REPO/pulls/PULL_NUMBER/comments | \
  jq '.[] | select(.path == "myfile.py" an
