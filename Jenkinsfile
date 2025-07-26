pipeline {
    agent any

    environment {
        // Azure OpenAI
        AZURE_OPENAI_ENDPOINT = credentials('AZURE_OPENAI_ENDPOINT')
        AZURE_OPENAI_DEPLOYMENT = credentials('AZURE_OPENAI_DEPLOYMENT')
        AZURE_OPENAI_VERSION = credentials('AZURE_OPENAI_VERSION')
        AZURE_OPENAI_KEY = credentials('AZURE_OPENAI_KEY')

        // GitHub
        GITHUB_REPO = 'your_org/your_repo'  // e.g., my-org/my-repo
        GITHUB_TOKEN = credentials('GITHUB_TOKEN')
        PR_ID = ''  // Will be set dynamically
    }

    triggers {
        githubPullRequest(
            orgWhitelist: ['your_org'],
            triggerPhrase: '.*',
            onlyTriggerPhrase: false,
            useGitHubHooks: true,
            permitAll: true
        )
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git fetch --all'
            }
        }

        stage('Get PR ID') {
            steps {
                script {
                    // Extract PR number from env or GIT_BRANCH
                    def prBranch = env.CHANGE_ID ?: env.BRANCH_NAME
                    env.PR_ID = prBranch
                    echo "PR ID is ${env.PR_ID}"
                }
            }
        }

        stage('Run PR Code Review') {
            steps {
                sh '''
                    python3 python/pr_code_review.py
                '''
            }
        }
    }
}
