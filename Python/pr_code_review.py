#!/usr/bin/env python3

import os
import sys
import subprocess
import requests
import json

# === GitHub Environment Variables ===

GITHUB_REPO = os.environ.get('GITHUB_REPO')  # e.g., my-org/my-repo
PR_ID = os.environ.get('PR_ID')              # GitHub PR number
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

# === Azure OpenAI ===

AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT = os.environ.get('AZURE_OPENAI_DEPLOYMENT')
AZURE_OPENAI_VERSION = os.environ.get('AZURE_OPENAI_VERSION')
AZURE_OPENAI_KEY = os.environ.get('AZURE_OPENAI_KEY')

def check_env(var, name):
    if not var:
        print(f" Missing env var: {name}")
        sys.exit(1)

for val, name in [
    (GITHUB_REPO, 'GITHUB_REPO'),
    (PR_ID, 'PR_ID'),
    (GITHUB_TOKEN, 'GITHUB_TOKEN'),
    (AZURE_OPENAI_ENDPOINT, 'AZURE_OPENAI_ENDPOINT'),
    (AZURE_OPENAI_DEPLOYMENT, 'AZURE_OPENAI_DEPLOYMENT'),
    (AZURE_OPENAI_VERSION, 'AZURE_OPENAI_VERSION'),
    (AZURE_OPENAI_KEY, 'AZURE_OPENAI_KEY'),
]:
    check_env(val, name)

# === Step 1: Get PR details from GitHub ===

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

pr_url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{PR_ID}"
r = requests.get(pr_url, headers=headers)

if r.status_code != 200:
    print(f" PR #{PR_ID} not found. Status: {r.status_code}")
    sys.exit(1)

pr_data = r.json()
base_branch = pr_data['base']['ref']
head_branch = pr_data['head']['ref']

print(f"📌 PR Base branch: {base_branch}")
print(f"📌 PR Head branch: {head_branch}")

# === Step 2: Generate diff ===

print("📂 Generating git diff...")
subprocess.run(["git", "fetch", "origin", base_branch], check=True)
subprocess.run(["git", "fetch", "origin", head_branch], check=True)

diff_cmd = ["git", "diff", f"origin/{base_branch}...origin/{head_branch}"]
with open("pr_diff.txt", "w") as f:
    subprocess.run(diff_cmd, stdout=f, check=True)

# === Step 3: Analyze with Azure OpenAI ===

with open("pr_diff.txt", "r") as f:
    diff_summary = f.read()

payload = {
    "messages": [
        {
            "role": "system",
            "content": "You are a senior code reviewer. Provide structured, detailed PR feedback per file."
        },
        {
            "role": "user",
            "content": f"Here are the PR changes:\n\n{diff_summary}\n\nFor each file, provide:\n1. Accurate changes summary.\n2. Modifications for changes summary.\n\nFormat:\n### File: filename\n\n#### Changes:\n- ...\n\n#### Modifications:\n- ...\n\nEnd with an overall review summary."
        }
    ]
}

openai_headers = {
    "Content-Type": "application/json",
    "api-key": AZURE_OPENAI_KEY
}

ai_url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_VERSION}"
ai_resp = requests.post(ai_url, headers=openai_headers, json=payload)

if ai_resp.status_code != 200:
    print(f" OpenAI failed. Status: {ai_resp.status_code}")
    print(ai_resp.text)
    sys.exit(1)

feedback = ai_resp.json()['choices'][0]['message']['content']

# === Step 4: Post GitHub PR Comment ===

print(" Posting feedback to GitHub PR...")

comment_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{PR_ID}/comments"
comment_payload = {
    "body": feedback
}

post_resp = requests.post(comment_url, headers=headers, json=comment_payload)

if post_resp.status_code != 201:
    print(f" Failed to post GitHub comment. Status: {post_resp.status_code}")
    print(post_resp.text)
    sys.exit(1)

print("Feedback posted to PR successfully.")
