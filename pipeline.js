console.log(process.argv[2]);
/*
const region =
const prcss = require('child_process');
const ssh = require('node-ssh');
const scanner = require('sonarqube-scanner');
const aws   = require('aws-sdk');
const secrets = require("@aws-sdk/client-secrets-manager");
const client = new AWS.SecretsManager({ region: "REGION" });

// Authenticate to AWS-SDK
AWS.config.update({
  accessKeyId: 'YOUR_ACCESS_KEY_ID',
  secretAccessKey: 'YOUR_SECRET_ACCESS_KEY',
  region: 'eu-west-1'
});


const ec2   = new AWS.EC2();
const ssm   = new AWS.SSM();

console.log('running sonarqube')
scanner({
    serverUrl : 'https://52.15.103.252',
    token : '',
    options: {
      'sonar.projectName': 'NodeGoat Example',
      'sonar.projectDescription': 'This project is just for testing',
      'sonar.sources': 'NodeGoat'
    }},() => prcss.exit()
)
console.log('running semgrep')
prcss.exec('semgrep --config "p/nodejsscan" .', (error, stdout, stderr) => {
	console.log('stdout: '+ stdout);
	console.log('stderr: '+ stderr);
	if (error !== null) {
		console.log('exec error: ' + error);
	}
});
console.log('fetching instances...')
ec2.describeInstances({},function(err, data) {
  if (err) {
    console.error(err);
  } else {
    for(let i in data.Reservations){
      for(let j in data.Reservations[i]["Instances"]){
        k=data.Reservations[i]["Instances"][j]
        //console.log(k["Tags"])
        console.log(k["InstanceType"]+"\t"+k["PublicIpAddress"]+"\t"+k["PrivateIpAddress"]+"\t"+k["State"]["Name"]+"\t"+k["KeyName"])
      }
    }
  }
});
ssh.connect({
  host: 'localhost',
  username: 'steel',
  privateKeyPath: '/home/steel/.ssh/id_rsa'
});
ssh.putDirectory('/talos', '/home/talos', {
  recursive: true,
  concurrency: 10
});

//Remove Secrets
AWS.config.update({
  accessKeyId: '---------------------',
  secretAccessKey: '----------------------------------',
});
*/