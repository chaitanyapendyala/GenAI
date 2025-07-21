pipeline {
  agent any

  environment {
    AZURE_OPENAI_ENDPOINT = 'https://bindh-maaplwo0-eastus2.cognitiveservices.azure.com'
    DEPLOYMENT_NAME       = 'gpt-35-turbo'
    API_VERSION           = '2025-01-01-preview'
    AZURE_OPENAI_APIKEY   =  credentials('AZURE_OPENAI_APIKEY')
    BUILD_CONFIGURATION   = 'Release'
    SOLUTION_PATTERN      = '**/*.sln'
    ARTIFACT_OUTPUT       = 'publish_output'
  }

  stages {
    stage('🔍 AI Analyze Jenkinsfile') {
      steps {
        script {
          def groovyContent = readFile('Jenkinsfile')
          def prompt = """
You are a Jenkins pipeline expert. Review the following Jenkinsfile and provide:

### ❌ Issues
- List misconfigurations, deprecated syntax, missing inputs, errors, security problems.

### 🔍 Recommendations
- Suggestions to improve code quality, performance, security, maintainability.

${groovyContent}
"""
          def body = groovy.json.JsonOutput.toJson([
            messages: [
              [role: 'system', content: 'You are an expert Jenkins pipeline reviewer.'],
              [role: 'user',   content: prompt]
            ]
          ])
          def response = httpRequest(
            httpMode: 'POST',
            contentType: 'APPLICATION_JSON',
            url: "${AZURE_OPENAI_ENDPOINT}/openai/deployments/${DEPLOYMENT_NAME}/chat/completions?api-version=${API_VERSION}",
            customHeaders: [
              [name: 'api-key', value: AZURE_OPENAI_APIKEY],
              [name: 'Content-Type', value: 'application/json']
            ],
            requestBody: body,
            validResponseCodes: '200'
          )
          def result = readJSON text: response.content
          echo "\n=== ✅ AI Analysis ===\n${result.choices[0].message.content}"
        }
      }
    }

    stage('🔧 Build .NET Application') {
      steps {
        echo 'Restoring NuGet packages…'
        sh 'dotnet restore ${SOLUTION_PATTERN}'

        echo 'Building solution…'
        sh 'dotnet build --configuration ${BUILD_CONFIGURATION}'

        echo 'Publishing project…'
        sh 'dotnet publish --configuration ${BUILD_CONFIGURATION} --output ${ARTIFACT_OUTPUT}'

        echo '🔁 Archiving artifacts…'
        archiveArtifacts artifacts: "${ARTIFACT_OUTPUT}/**/*", fingerprint: true
      }
    }
  }

  post {
    always {
      echo "✅ Pipeline completed."
    }
  }
}

