pipeline {
    agent any

    environment {
        GITHUB_TOKEN            = credentials('github-pat')
        AZURE_OPENAI_ENDPOINT   = credentials('azure-openai-endpoint')
        AZURE_OPENAI_DEPLOYMENT = credentials('azure-openai-deployment')
        AZURE_OPENAI_VERSION    = credentials('azure-openai-version')
        AZURE_OPENAI_KEY        = credentials('azure-openai-key')
    }

    stages {
        stage('Checkout and Setup') {
            steps {
                checkout scm
                script {
                    def gitUrl = sh(script: 'git config --get remote.origin.url', returnStdout: true).trim()
                    def match = gitUrl =~ /[:\/]([^\/]+\/[^\/\.]+)(\.git)?$/
                    if (match) {
                        env.GITHUB_REPO = match[0][1]  // org/repo
                        echo "📦 GitHub Repo: ${env.GITHUB_REPO}"
                    } else {
                        error("❌ Could not parse GitHub repo from URL: ${gitUrl}")
                    }

                    if (env.CHANGE_ID) {
                        env.PR_ID = env.CHANGE_ID
                        echo "🔍 Detected PR ID: ${env.PR_ID}"
                    } else {
                        error("❌ This pipeline only works for Pull Requests.")
                    }

                    sh 'git fetch origin +refs/heads/*:refs/remotes/origin/*'
                }
            }
        }

        stage('Run AI Code Review (Python)') {
            steps {
                sh """
                    python3 python/pr_code_review.py \
                        --repo ${GITHUB_REPO} \
                        --pr ${PR_ID} \
                        --token ${GITHUB_TOKEN} \
                        --openai-endpoint ${AZURE_OPENAI_ENDPOINT} \
                        --deployment ${AZURE_OPENAI_DEPLOYMENT} \
                        --api-version ${AZURE_OPENAI_VERSION} \
                        --openai-key ${AZURE_OPENAI_KEY}
                """
            }
        }
    }
}
