const scanner = require('sonarqube-scanner');
const process = require('child_process');
console.log('running sonarqube')
scanner({
    serverUrl : 'https://52.15.103.252',
    token : '',
    options: {
      'sonar.projectName': 'NodeGoat Example',
      'sonar.projectDescription': 'This project is just for testing',
      'sonar.sources': 'NodeGoat'
    }},() => process.exit()
)
console.log('running semgrep')
process.exec('semgrep --config "p/nodejsscan" .', (error, stdout, stderr) => {
	console.log('stdout: '+ stdout);
	console.log('stderr: '+ stderr);
	if (error !== null) {
		console.log('exec error: ' + error);
	}
});
