//-----------------------------------------
// node pipeline.js argv[2:N]
//-----------------------------------------
// process.argv[2]: AWS access key id
// process.argv[3]: AWS access secret
// process.argv[4]: Project name
// process.argv[5]: Release name
// process.argv[6]: Action ("Once","Deploy","Rollback")
// process.argv[7]: Migrations ("Yes","No")

//-----------------------------------------
// Required modules
//-----------------------------------------
const scanner        = require('sonarqube-scanner');
const prcss          = require('child_process');
const simpleGit      = require('simple-git');
const ssh            = require('node-ssh');
const aws            = require('aws-sdk');

//-----------------------------------------
// Initialization
//-----------------------------------------
// Setup authentication for AWS-SDK
aws.config.update({
  accessKeyId: process.argv[2],
  secretAccessKey: process.argv[3],
  region: 'eu-west-1'
});
// Initialize AWS client objects
const client = {
  'ec2': new aws.EC2(),
  'sec': new aws.SecretsManager()
}
// Shut up AWS
require('aws-sdk/lib/maintenance_mode_message').suppress = true;

// Run pipeline
pipeline();

aws.config.update({
  accessKeyId: 'EMPTYEMPTYEMPTY',
  secretAccessKey: 'EMPTYEMPTYEMPTY',
});

//-----------------------------------------
// Core pipeline logic
//-----------------------------------------
async function pipeline(){
  let Resources = await GatherResources(client,process.argv[4],process.argv[5]);
  //SAST(Resources['Deploy']);
  await Optimize(Resources['Deploy']);
  switch(process.argv[6]){
    case 'Once':
      // Randomly pick an instance to test release.
      const First = Resources['Instances'][Math.floor(Math.random()*Resources['Instances'].length)]
      await Deploy(Resources['SSH'],Resources['Deploy'],[First],[
        `cd ~/${Resources['Deploy']}`,
        `npm install`,
        process.argv[7]==='Yes'?'npm run migrate -- --production':'echo "No migrations"',
        'sleep 5',
        'node config.js',
        'pm2 stop old_test',
        `pm2 start "npm run ${process.argv[4]}-prod" --namespace "new_test"`,
        'pm2 logs new_test'
      ]);
    break;
    case 'Deploy':
      await Deploy(Resources['SSH'],Resources['Deploy'],Resources['Instances'],[
        `cd ~/${Resources['Deploy']}`,
        'node config.js',
        'pm2 stop all',
        'pm2 delete all',
        `pm2 start "npm run ${process.argv[4]}-prod" --namespace "old_test"`,
        `pm2 start "npm run ${process.argv[4]}-prod"`,
        `pm2 start "npm run ${process.argv[4]}-prod"`,
        `pm2 start "npm run ${process.argv[4]}-prod"`,
        `pm2 start "npm run ${process.argv[4]}-prod"`,
        `pm2 start "npm run ${process.argv[4]}-prod"`,
        `pm2 start "npm run ${process.argv[4]}-prod"`,
        `pm2 start "npm run ${process.argv[4]}-prod"`
        ]);
    break;
    case 'Rollback':
      await Deploy(Resources['SSH'],Resources['Deploy'],Resources['Instances'],[
        `cd ~/${Resources['Deploy']}`,
        'pm2 stop new_test',
        'pm2 delete new_test',
        'pm2 start old_test',
        'pm2 reload all'
        ]);
  }
  await Cleanup(Resources);
}

// Deploy
async function Deploy(SSH,release,instances,commands){
  try { for(let instance of instances){
    const ssh = new NodeSSH();
    await ssh.connect({host: instance, username:'ubuntu', privateKey: SSH})
    console.log(`[INFO] Deploying ${release} > ${instances}`);
    const result = await ssh.putDirectory(release,`~/${release}`);
    if(!result){ throw '[ERROR] failed to copy directory' }
    for(let command of commands){
      let {stdout,stderr} = await ssh.execCommand(command);
      if(stderr){ throw `[ERROR] failed to execute ${command}` }
    }
    await ssh.dispose();
  }}catch(err){console.log('[ERROR] failed to deploy',err);}
}

// Optimize
async function Optimize(source_code){
  // Todo/
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
  prcss.exec(`semgrep --config "p/nodejsscan" ./'${source_code}`, (error, stdout, stderr) => {
    console.log('stdout: '+ stdout);
    console.log('stderr: '+ stderr);
    if (error !== null) {
      console.log('[WARN] FAILED at stage: Semgrep with:',err);
    }
  });
  // Other security things
}

// Gather resources
async function GatherResources(client,project,branch){
  // All these run in parellal
  const result = await Promise.all([ (async (client) => { try {
        // Get all instances
        console.log('[INFO] running stage: Get_Instances');
        return await FindByTag(client,`prod-p-${project}-inst`);
  }catch(err){console.log('[ERROR] failed to fetch instances',err);}})(client['ec2'],project),
  (async (project,branch) => { try {
        // Fetch the repository token
        console.log('[INFO] running stage: Clone_Checkout');
        let response = await client['sec'].getSecretValue({SecretId: `RepoToken_${project}`}).promise();
        // Clone and checkout current with branch name as the directory 
        await simpleGit().clone(
            `http://sinnan:${response.SecretString}@artifactory.devcrud.uk/org/${project}.git`,
            `./${branch}`,
            ['--branch',branch]);
        response = '';
        return Promise.resolve(branch);
  }catch(err){console.log('[ERROR] failed to fetch repositories',err);}})(project,branch),
  (async (client,project) => { try {
        // Fetch secrets for project
        console.log('[INFO] running stage: Get_Secrets');
        const response = await client.getSecretValue({SecretId: `ProdSshKey_${project}`}).promise();
        //Res['SSH'] = response.SecretString;
        return Promise.resolve(response.SecretString);
  }catch(err){console.log('[ERROR] failed to fetch secrets',err);}})(client['sec'],project)])
  // Object of all the resources gathered so far
  return {'SSH':result[2],'Deploy':result[1],'Instances':result[0]};
}

// Find instance in the instance list
async function FindByTag(ec2,instance_tag){
    let InstancePrivateIps=[];
    // Call the describeInstances() method and await the response
    const data = await ec2.describeInstances().promise();
    // Log the instance information
    for(let element of data.Reservations){
      for(let tag of element['Instances'][0]['Tags']){
        if(tag['Value']===instance_tag && element['Instances'][0]['State']['Name']==='running'){
          InstancePrivateIps.push(element['Instances'][0]['PrivateIpAddress']);
        }
      }
    }
    if(InstancePrivateIps.length>0){
      return InstancePrivateIps;
    }
    throw 'No instances found';
}