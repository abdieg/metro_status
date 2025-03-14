pipeline {
	agent any

	stages {

		stage('Clone repository') {
			steps {
				echo 'Cloning the repository...'
				git url: 'https://github.com/abdieg/metro_status.git', branch: 'main'
				echo 'Repository cloned successfully.'
			}
		}

		stage('Prepare environment variables') {
            steps {
                withCredentials([
                    string(credentialsId: 'ntfy_ip', variable: 'NTFY_IP'),
                    string(credentialsId: 'ntfy_port', variable: 'NTFY_PORT'),
                ]) {
                    script {
                        def envContent = """NTFY_IP=${env.NTFY_IP}
                                            NTFY_PORT=${env.NTFY_PORT}
                                            """
                        writeFile file: '.env', text: envContent
                        echo "Created .env file with hidden environment variables."
                    }
                }
            }
        }

		stage('Set Permissions') {
			steps {
				echo 'Setting execute permissions on scripts...'
				sh 'chmod +x ./d.build.sh'
				sh 'chmod +x ./d.run.sh'
				echo 'Permissions set successfully.'
			}
		}

		stage('Build Docker Image') {
			steps {
				echo 'Building the Docker image...'
				sh './d.build.sh'
				echo 'Docker image built successfully.'
			}
		}

		stage('Deploy') {
			steps {
				echo 'Deploying the application...'
				echo 'Automatically stop and delete old container to create and run the new one...'
				sh './d.run.sh'
				echo 'Deployment completed successfully.'
			}
		}

	}
}