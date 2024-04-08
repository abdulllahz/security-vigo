//DEPENDENCY
const express = require('express');
const postgres = require('pg');
const crypto = require('crypto');
const bodyparser = require('body-parser')
var secp = ''

//CONFIG
var client = ''
const secret = "SECRET";
const expiry = 300;
const port = 3000;

//INIT
const app = express();
app.use(bodyparser.json());
(async () => {
secp=await import('@noble/secp256k1');
while (true) {
    try {
      client = new postgres.Client({user: 'bykea',password: 'bykea_123',host: 'db',database: 'authentication',port: 5432});
      await client.connect();
      console.log('Connected to the database successfully!');
      break; // Exit the loop if the connection is successful
    } catch (error) {
      console.error('Failed to connect to the database:', error.message);
      await new Promise((resolve) => setTimeout(resolve, 3000));
    }
}
app.listen(port, () => {
  console.log(`service is running on http://127.0.0.1:${port}`);
});
})();

//SERVICES
async function InsertIdentity(client,pubkey){
	await client.query('INSERT INTO records(fingerprint, key) VALUES($1, $2)', [await GenerateIdentityFingerprint(pubkey),pubkey]);
}

async function GetPubKeyFromFingerprint(client,id) {
  const result=await client.query("SELECT key FROM records WHERE key=$1;",[id]);
  return result.rows[0].key
}

async function StampPuzzle(secret,puzzle){
  return crypto
  .createHash("sha256")
  .update(JSON.stringify(puzzle))
  .update(secret)
  .digest("hex");
}

async function SeedPuzzle(length){
  return crypto
  .randomBytes(length)
  .toString("base64");
}

async function SchnorrVerify(client,solution,puzzle,id){
  solution.r=BigInt(solution.r);
  solution.s=BigInt(solution.s);
  var key=new Uint8Array(atob(await GetPubKeyFromFingerprint(client,id)).split('').map(char => char.charCodeAt(0)));
  return (await secp.verify(
	solution,
	await crypto.createHash("sha256").update(JSON.stringify(puzzle)).digest("hex"),
	await key
  ));
}

async function GenerateIdentityFingerprint(pubkey){
  return crypto
  .createHash("sha256")
  .update(pubkey)
  .digest("hex");
}

//CONTROLLERS
app.get("/HeartBeat",async (req, res) => {
  console.log("HeartBeat");
  res.json({msg:"alive"});
});

app.post("/RegisterKey",async (req, res) => {
  console.log("RegisterKey");
  console.log(req.body);
  response={msg:""}
  try{
  	InsertIdentity(client,req.body.pubkey);
  	response.msg="success";
  }catch(e){response.msg=e;}
  console.log(response);
  res.json(response);
});

app.get("/GenerateChallenge",async (req, res) => {
  console.log("GenerateChallenge");
  console.log(`{ identity: '${decodeURI(req.query.identity)}' }`);
  response={msg:""}
  let expiry_date = new Date();
  expiry_date.setSeconds(expiry_date.getSeconds()+expiry);
  let seed=await SeedPuzzle(16);
  let puzzle={
   	"id":req.query.identity,
    "seed":seed,
    "expiry":expiry_date
  };
  response.puzzle=puzzle;
  response.stamp=await StampPuzzle(secret,puzzle);
  console.log(response);
  res.json(response);
});

app.post("/CheckSolution",async (req, res) => {
  console.log("CheckSolution");
  console.log(req.body);
  response={msg:""}
  try{
  	if(req.body.stamp!==await StampPuzzle(secret,req.body.puzzle))     
      {throw new Error('Puzzle Inconsistent!');}
  	if(Date()>Date(req.body.puzzle.expiry))
      {throw new Error('Puzzle Expired!');}
    if(!(await SchnorrVerify(client,req.body.solution,req.body.puzzle,req.body.puzzle.id)))
      {throw new Error('Solution Incorrect!');}
    response.msg="success";
  }catch(e){console.log(e);response.msg=e;}
  console.log(response);
  res.json(response);
});