pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
  }

  parameters {
    booleanParam(name: 'SKIP_INGESTION', defaultValue: false, description: 'Skip GitHub ingestion and reuse existing raw data')
    booleanParam(name: 'CONTINUE_ON_ERROR', defaultValue: false, description: 'Continue workflow even if one step fails')
    booleanParam(name: 'EXPORT_ST_READY', defaultValue: true, description: 'Export ST-ready JSON files after workflow')
    string(name: 'TARGET_REPO', defaultValue: 'STM32CubeH7', description: 'Repo name for ST-ready export (e.g., STM32CubeH7, STM32CubeH5)')
    string(name: 'PYTHON_BIN', defaultValue: 'python', description: 'Python executable available on Jenkins agent')
  }

  environment {
    GITHUB_TOKEN = credentials('github-token')
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Setup Python Env') {
      steps {
        script {
          bat "${params.PYTHON_BIN} -m venv .venv"
          bat ".venv\\Scripts\\python -m pip install --upgrade pip"
          bat ".venv\\Scripts\\python -m pip install requests jsonschema"
        }
      }
    }

    stage('Run Full Workflow') {
      steps {
        script {
          def cmd = '.venv\\Scripts\\python -m pipeline.run_full_workflow'
          if (params.SKIP_INGESTION) {
            cmd = cmd + ' --skip-ingestion'
          }
          if (params.CONTINUE_ON_ERROR) {
            cmd = cmd + ' --continue-on-error'
          }
          if (params.EXPORT_ST_READY) {
            cmd = cmd + ' --export-st-ready'
          }
          bat cmd
        }
      }
    }

    stage('Schema Validation Gate') {
      steps {
        bat '.venv\\Scripts\\python -m pipeline.evaluation.validate_schemas'
      }
    }

    stage('Archive Artifacts') {
      steps {
        archiveArtifacts artifacts: 'data/*.json, datasets/07_delivery/st_ready/**/*.json, datasets/06_eval_outputs/*.csv', allowEmptyArchive: true, fingerprint: true
      }
    }
  }

  post {
    success {
      echo 'STM32Cube preprocessing pipeline completed successfully.'
    }
    failure {
      echo 'Pipeline failed. Check stage logs and schema validation output.'
    }
    always {
      echo 'Build finished.'
    }
  }
}
