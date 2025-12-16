pipeline {
    agent any

    environment {
        PYTHON_VERSION = "3.13.3"
        IMAGE_NAME = "project_r"
        IMAGE_TAG = "build-${env.BUILD_NUMBER}"
    }

    stages {

        stage('Clone Repo') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python + Poetry') {
            steps {
                sh """
                python3 -m venv venv
                . venv/bin/activate
                pip install --upgrade pip
                pip install poetry
                """
            }
        }

        stage('Install Dependencies (Poetry)') {
            steps {
                sh """
                . venv/bin/activate
                poetry install --no-interaction --no-root
                """
            }
        }
        stage('Lint (ruff)'){
            sh"""
                . venv/bin/activate
                poetry run ruff check .
                """
        }

        stage('Build Docker Image') {
            steps {
                sh """
                docker build \
                    -t ${IMAGE_NAME}:${IMAGE_TAG} \
                    -t ${IMAGE_NAME}:latest .
                """
            }
        }
    }
}
