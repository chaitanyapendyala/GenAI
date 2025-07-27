pipeline {
    agent any

    environment {
        AZURE_OPENAI_ENDPOINT    = credentials('AZURE_OPENAI_ENDPOINT ')
        AZURE_OPENAI_DEPLOYMENT  = credentials('AZURE_OPENAI_DEPLOYMENT')
        AZURE_OPENAI_VERSION     = credentials('AZURE_OPENAI_VERSION')
        AZURE_OPENAI_KEY         = credentials('AZURE_OPENAI_KEY')
        GITHUB_TOKEN             = credentials('GITHUB_TOKEN ')  // GitHub PAT with "repo" access
    }

    stages {
        stage('Initialize') {
            steps {
                checkout scm

                script {
                    // Extract GitHub repo from git config
                    def gitUrl = sh(script: 'git config --get remote.origin.url', returnStdout: true).trim()
                    def match = gitUrl =~ /[:\/]([^\/]+\/[^\/\.]+)(\.git)?$/
                    if (match) {
                        env.GITHUB_REPO = match[0][1]  // Format: org/repo
                        echo "📦 GitHub Repo: ${env.GITHUB_REPO}"
                    } else {
                        error("❌ Could not parse GitHub repo from URL: ${gitUrl}")
                    }

                    // Detect PR ID from GitHub PR plugin
                    if (env.CHANGE_ID) {
                        env.PR_ID = env.CHANGE_ID
                        echo "🔍 Detected PR ID: ${env.PR_ID}"
                    } else {
                        error("❌ This pipeline only works for Pull Requests.")
                    }

                    // Fetch all branches
                    sh 'git fetch origin +refs/heads/*:refs/remotes/origin/*'
                }
            }
        }

        stage('Generate PR Diff') {
            steps {
                script {
                    def base = "origin/${env.CHANGE_TARGET}"
                    def head = "origin/${env.CHANGE_BRANCH}"
                    echo "📄 Diffing: ${base}...${head}"
                    sh "git diff ${base}...${head} > pr_diff.txt"
                }
            }
        }

        stage('Review with Azure OpenAI') {
            steps {
                script {
                    def diff = readFile('pr_diff.txt')

                    def payload = [
                        messages: [
                            [ role: "system", content: "You are a senior code reviewer. Provide detailed review per file." ],
                            [ role: "user", content: "Here is the diff:\n\n${diff}\n\nGive comments per file, list improvements and an overall summary." ]
                        ]
                    ]

                    def response = httpRequest(
                        url: "${AZURE_OPENAI_ENDPOINT}/openai/deployments/${AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version=${AZURE_OPENAI_VERSION}",
                        httpMode: 'POST',
                        customHeaders: [[name: 'Content-Type', value: 'application/json'], [name: 'api-key', value: AZURE_OPENAI_KEY]],
                        requestBody: groovy.json.JsonOutput.toJson(payload),
                        validResponseCodes: '200',
                        consoleLogResponseBody: false
                    )

                    def analysis = new groovy.json.JsonSlurper().parseText(response.content)
                    env.AI_FEEDBACK = analysis.choices[0].message.content
                    writeFile file: 'ai_review.txt', text: env.AI_FEEDBACK
                }
            }
        }

        stage('Post Feedback to GitHub PR') {
            steps {
                script {
                    def commentBody = [ body: env.AI_FEEDBACK ]
                    def postUrl = "https://api.github.com/repos/${env.GITHUB_REPO}/issues/${env.PR_ID}/comments"

                    httpRequest(
                        url: postUrl,
                        httpMode: 'POST',
                        customHeaders: [
                            [name: 'Authorization', value: "Bearer ${GITHUB_TOKEN}"],
                            [name: 'Content-Type', value: 'application/json']
                        ],
                        requestBody: groovy.json.JsonOutput.toJson(commentBody),
                        validResponseCodes: '201'
                    )
                    echo "✅ Feedback posted to GitHub PR #${env.PR_ID}"
                }
            }
        }
    }
}
