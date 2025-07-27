import argparse
import subprocess
import requests
import json
import os

def get_diff(base_branch, head_branch):
    subprocess.run(['git', 'fetch', 'origin', base_branch, head_branch], check=True)
    diff = subprocess.check_output(['git', 'diff', f'origin/{base_branch}', f'origin/{head_branch}'])
    return diff.decode()

def call_azure_openai(endpoint, deployment, api_version, key, diff):
    headers = {
        "Content-Type": "application/json",
        "api-key": key
    }
    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    payload = {
        "messages": [
            {"role": "system", "content": "You are a senior code reviewer. Provide file-wise suggestions and then an overall summary."},
            {"role": "user", "content": f"Here is the code diff:\n\n{diff}"}
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

def comment_on_pr(repo, pr_id, token, comment):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"https://api.github.com/repos/{repo}/issues/{pr_id}/comments"
    data = {"body": comment}
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--pr', required=True)
    parser.add_argument('--token', required=True)
    parser.add_argument('--openai-endpoint', required=True)
    parser.add_argument('--deployment', required=True)
    parser.add_argument('--api-version', required=True)
    parser.add_argument('--openai-key', required=True)
    args = parser.parse_args()

    base_branch = os.environ.get('CHANGE_TARGET', 'main')
    head_branch = os.environ.get('CHANGE_BRANCH', 'feature')

    print(f"🔍 Getting diff between {base_branch} and {head_branch}...")
    diff = get_diff(base_branch, head_branch)
    print("✅ Diff generated")

    print("🤖 Analyzing with Azure OpenAI...")
    feedback = call_azure_openai(args.openai_endpoint, args.deployment, args.api_version, args.openai_key, diff)
    print("✅ Review feedback received")

    print("📬 Posting review to GitHub PR...")
    comment_on_pr(args.repo, args.pr, args.token, feedback)
    print("✅ Comment posted successfully")

if __name__ == '__main__':
    main()
