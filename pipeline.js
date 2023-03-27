// Application parameters:
// process.argv[2]: AWS access key id
// process.argv[3]: AWS access secret
// process.argv[4]: Release to deploy
// process.argv[5]: Release to rollback to

console.log("[INFO] Fresh release"+process.argv[4]);
console.log("[INFO] Fallback release"+process.argv[5]);

const prcss          = require('child_process');
const ssh            = require('node-ssh');
const scanner        = require('sonarqube-scanner');
const aws            = require('aws-sdk');
const secrets        = require("@aws-sdk/client-secrets-manager");
const simpleGit = require('simple-git');
var TalosPrivateKey  = ''

// Setup authentication for AWS-SDK
AWS.config.update({
  accessKeyId: process.argv[2],
  secretAccessKey: process.argv[3],
  region: 'eu-west-1'
});

// Initialize AWS client objects
const aws = {
  'ec2': new AWS.EC2(),
  'ssm': new AWS.SSM(),
  'sec': new AWS.SecretsManager()
}

// Fetch secrets for Talos
try{
  var response = await aws['sec'].getSecretValue({SecretId: 'my-secret-id'}).promise();
  TalosPrivateKey = response.SecretString;
} catch (err) {
    console.log("[ERROR] FAILED at stage: Get_Secrets with:"+err);
}

// Clone and checkout current and rollback release repo
await SyncClone([process.argv[4],process.argv[5]]);

// Trigger a sonarqube analysis
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

// Trigger a semgrep analysis
console.log('running semgrep')
prcss.exec('semgrep --config "p/nodejsscan" .', (error, stdout, stderr) => {
	console.log('stdout: '+ stdout);
	console.log('stderr: '+ stderr);
	if (error !== null) {
		console.log("[WARN] FAILED at stage: Semgrep with:"+err);
	}
});

// Deploy Once
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

// Clone Repos function
async function SyncClone(branches){
  for(branch of branches){
    cloneRepo('http://artifactory.devcrud.uk/org/talos.git','./'+branch,['--branch',branch]);
  }
  return true;
}

//await checkoutBranch(branchName, { cwd: localPath });
/*
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