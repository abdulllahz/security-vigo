//-----------------------------------------
// node pipeline.js Argv[3:N]
//-----------------------------------------
// process.argv[2]: AWS access key id
// process.argv[3]: AWS access secret
// process.argv[4]: Release to deploy
// process.argv[5]: Release to rollback
// process.argv[6]: Action ("Once","Deploy","Rollback")

//-----------------------------------------
// Required modules
//-----------------------------------------
const prcss          = require('child_process');
//const ssh            = require('node-ssh');
const scanner        = require('sonarqube-scanner');
const aws            = require('aws-sdk');
const simpleGit      = require('simple-git');
var TalosPrivateKey  = ''


pipeline();

//-----------------------------------------
// Initialization
//-----------------------------------------
// Setup authentication for AWS-SDK
AWS.config.update({
  accessKeyId: process.argv[2],
  secretAccessKey: process.argv[3],
  region: 'eu-west-1'
});
// Initialize AWS client objects
const client = {
  'ec2': new AWS.EC2(),
  'sec': new AWS.SecretsManager()
}

//-----------------------------------------
// Core pipeline login
//-----------------------------------------
async function pipeline(){
  var Resources = await GatherResources(client,process.argv[4],process.argv[5]);
  //SAST(Resources["Deploy"]);
  await Optimize(Resources["Deploy"]);
  switch(process.argv[6]){
    case "Once":
      const First = Resources["Instances"][Math.floor(Math.random()*Resources["Instances"].length)]
      await Deploy(
        Resources["Deploy"],
        [First]
      );
    break;
    case "Deploy":
      await Deploy(
        Resources["Deploy"],
        Resources["Instances"]
      );
    break;
    case "Rollback":
      await Deploy(
        Resources["Rollback"],
        Resources["Instances"]
      );
  }
}

// Deploy
async function Deploy(release,instances){
  console.log(release+" > "+instances);
}

// Optimize
async function Optimize(source_code){
  // Todo
}

// Source scan
function SAST(source_code){
  // Trigger a sonarqube analysis
  console.log('[INFO] running stage: Scan_Sonarqube')
  scanner({
    serverUrl : 'https://52.15.103.252',
    token : '',
    options: {
      'sonar.projectName': 'NodeGoat Example',
      'sonar.projectDescription': 'This project is just for testing',
      'sonar.sources': source_code
    }},() => prcss.exit()
  )
  // Trigger a semgrep analysis
  console.log('[INFO] running stage: Scan_Semgrep')
  prcss.exec('semgrep --config "p/nodejsscan" ./'+source_code, (error, stdout, stderr) => {
    console.log('stdout: '+ stdout);
    console.log('stderr: '+ stderr);
    if (error !== null) {
      console.log("[WARN] FAILED at stage: Semgrep with:"+err);
    }
  });
  // Other security things
}

// Gather resources
async function GatherResources(client,deploy,rollback){
  
  // Information
  Res={"SSH":"EMPTY","Deploy":deploy,"Rollback":rollback,"Instances":[]}

  // Fetch secrets for Talos
  console.log('[INFO] running stage: Get_Secrets')
  try{ 
    const response = client['sec'].getSecretValue({SecretId: 'TalosProdSshKey'}).promise();
    Res["SSH"] = response.SecretString;
  } catch (err) {
    console.log("[ERROR] FAILED at stage: Get_Secrets with:"+err);
  }
  
  // Get all instances
  console.log('[INFO] running stage: Get_Instances')
  try {
    Res["Instances"] = FindByTag(client['ec2'],"prod-p-talos-inst");
    console.log('[INFO] talos instances: '+Res["Instances"]);
  } catch (err) {
    console.log("[ERROR] FAILED at stage: Get_Instances with:"+err);
  }
  
  // Clone and checkout current and rollback release repo
  console.log('[INFO] running stage: Clone_Checkout')
  try {
    SyncClone([deploy,rollback]);
  } catch (err) {
    console.log("[ERROR] FAILED at stage: Clone_Checkout with:"+err);
  }

  return Res;
}

// Clone repos synchronously
async function SyncClone(branches){
  for(branch of branches){
    cloneRepo('http://artifactory.devcrud.uk/org/talos.git','./'+branch,['--branch',branch]);
  }
  return true;
}

// Find talos in the instance list
async function FindByTag(ec2,instance_tag){
  const data = await ec2.describeInstances().promise();
  var add=[];
  for(let i in data.Reservations){
    for(let j in data.Reservations[i]["Instances"]){
      let k=data.Reservations[i]["Instances"][j];
      let l="";
      for(l in k["Tags"]){
        if(k["Tags"][l]["Key"]=="Name"){break;}
      }
      if(k["Tags"][l]["Value"]==instance_tag){
        add.push(k["PrivateIpAddress"]);
      }
    }
  }
  return add;
}

/*
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