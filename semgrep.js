var exec = require('child_process').exec;
console.log('running semgrep')
exec('semgrep --config "p/nodejsscan" .', (error, stdout, stderr) => {
	console.log('stdout: '+ stdout);
	console.log('stderr: '+ stderr);
	if (error !== null) {
		console.log('exec error: ' + error);
	}
});
