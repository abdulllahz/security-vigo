const scanner = require('sonarqube-scanner');
console.log('running sonarqube')
scanner({
    serverUrl : '52.15.103.252',
    token : '',
    options: {
      'sonar.projectName': 'NodeGoat Example',
      'sonar.projectDescription': 'This project is just for testing',
      'sonar.sources': 'NodeGoat'
    }},() => process.exit()
)
