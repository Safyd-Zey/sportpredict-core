// SportPredict Core: CI on every commit of every branch, CD to Kubernetes from main.
// Jenkins controller and job are defined as code in jenkins/ (see jenkins/setup.sh).

pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds()
    }

    environment {
        IMAGE = 'sportpredict-api'
        DOCKER_BUILDKIT = '1'
        PIP_CACHE_DIR = '/var/jenkins_home/.cache/pip'
        PIP_DISABLE_PIP_VERSION_CHECK = '1'
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    env.SHORT_SHA = sh(script: 'git rev-parse --short=7 HEAD', returnStdout: true).trim()
                    env.VERSION = sh(script: "grep -m1 '^version' pyproject.toml | cut -d'\"' -f2",
                                     returnStdout: true).trim()
                    currentBuild.description = "v${env.VERSION} @ ${env.SHORT_SHA}"
                }
                sh 'git log -1 --format="%h %an: %s"'
            }
        }

        stage('Quality gates') {
            parallel {
                stage('Lint (ruff)') {
                    agent { docker { image 'python:3.12-slim'; reuseNode true } }
                    steps {
                        sh '''
                            python -m venv /tmp/venv && . /tmp/venv/bin/activate
                            pip install -q "ruff>=0.6"
                            ruff check . && ruff format --check .
                        '''
                    }
                }
                stage('Unit tests (pytest)') {
                    agent { docker { image 'python:3.12-slim'; reuseNode true } }
                    steps {
                        sh '''
                            python -m venv /tmp/venv && . /tmp/venv/bin/activate
                            pip install -q -e ".[dev]"
                            mkdir -p reports
                            pytest -o addopts="" --junitxml=reports/junit.xml \
                                --cov=sportpredict --cov-report=term --cov-report=xml:reports/coverage.xml \
                                --cov-fail-under=85
                        '''
                    }
                    post {
                        always {
                            junit 'reports/junit.xml'
                            recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'reports/coverage.xml']],
                                           sourceDirectories: [[path: 'src']])
                        }
                    }
                }
                stage('Dockerfile lint (hadolint)') {
                    steps {
                        sh 'docker run --rm -i hadolint/hadolint:v2.15.1 hadolint --failure-threshold warning - < Dockerfile'
                    }
                }
            }
        }

        stage('Build image') {
            steps {
                sh '''
                    docker build \
                        --build-arg VERSION="$VERSION" --build-arg REVISION="$SHORT_SHA" \
                        -t "$IMAGE:$SHORT_SHA" .
                    docker image ls "$IMAGE:$SHORT_SHA"
                '''
            }
        }

        stage('Smoke test container') {
            steps {
                sh '''
                    c="sp-smoke-$SHORT_SHA-$BUILD_NUMBER"
                    docker run -d --name "$c" "$IMAGE:$SHORT_SHA"
                    trap 'docker rm -f "$c" >/dev/null' EXIT
                    docker exec -i "$c" python - http://127.0.0.1:8000 < scripts/smoke_test.py
                '''
            }
        }

        stage('Push to Docker Hub') {
            when {
                allOf {
                    branch 'main'
                    expression { env.DOCKERHUB_REPO?.trim() }
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub',
                                                  usernameVariable: 'DH_USER',
                                                  passwordVariable: 'DH_TOKEN')]) {
                    sh '''
                        echo "$DH_TOKEN" | docker login -u "$DH_USER" --password-stdin
                        for tag in "$SHORT_SHA" "$VERSION" latest; do
                            docker tag "$IMAGE:$SHORT_SHA" "$DOCKERHUB_REPO:$tag"
                            docker push "$DOCKERHUB_REPO:$tag"
                        done
                    '''
                }
            }
            post {
                always { sh 'docker logout || true' }
            }
        }

        stage('Deploy to Kubernetes (kind)') {
            when {
                allOf {
                    branch 'main'
                    expression { env.KIND_CLUSTER?.trim() }
                }
            }
            steps {
                withCredentials([file(credentialsId: 'kind-kubeconfig', variable: 'KUBECONFIG')]) {
                    sh '''
                        kind load docker-image "$IMAGE:$SHORT_SHA" --name "$KIND_CLUSTER"
                        sed "s|image: sportpredict-api:latest|image: $IMAGE:$SHORT_SHA|" k8s/sportpredict-api.yaml \
                            | kubectl apply -f -
                        kubectl -n sportpredict annotate deployment/sportpredict-api --overwrite \
                            kubernetes.io/change-cause="Jenkins build #$BUILD_NUMBER, commit $SHORT_SHA"
                        kubectl -n sportpredict rollout status deployment/sportpredict-api --timeout=180s
                    '''
                }
            }
        }

        stage('Verify deployment') {
            when {
                allOf {
                    branch 'main'
                    expression { env.KIND_CLUSTER?.trim() }
                }
            }
            steps {
                withCredentials([file(credentialsId: 'kind-kubeconfig', variable: 'KUBECONFIG')]) {
                    // Calls the API through the Service, i.e. the same route a client uses.
                    sh '''
                        kubectl -n sportpredict exec -i deploy/sportpredict-api -- \
                            python - http://sportpredict-api.sportpredict.svc < scripts/smoke_test.py
                        kubectl -n sportpredict get deploy,pods,svc -o wide
                        kubectl -n sportpredict rollout history deployment/sportpredict-api
                    '''
                }
            }
            post {
                failure {
                    withCredentials([file(credentialsId: 'kind-kubeconfig', variable: 'KUBECONFIG')]) {
                        sh 'kubectl -n sportpredict rollout undo deployment/sportpredict-api'
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs(deleteDirs: true, notFailBuild: true)
        }
    }
}
