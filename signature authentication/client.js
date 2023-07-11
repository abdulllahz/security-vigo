(async () => {
BigInt.prototype["toJSON"] = function (){return this.toString();};
const axios= (await import('axios')).default;
if (!globalThis.axios) globalThis.axios = axios;
var cryptoX = (await import('node:crypto')).webcrypto;
if (!globalThis.crypto) globalThis.crypto = cryptoX;
const secp = await import('@noble/secp256k1');

//save these locally
const base_url = "app:3000";
const privkey = secp.utils.randomPrivateKey(); //We can add other metrics here like OTP, FacialHashes...
const pubkey = secp.getPublicKey(privkey);
b64_privkey=btoa(String.fromCharCode(...privkey));
b64_pubkey=btoa(String.fromCharCode(...pubkey))
console.log("Save These Keys Locally!:\n\tPublic: "+b64_pubkey+"\n\tPrivate: "+b64_privkey);

while(!(await Connected(base_url))){/*Do Nothing and wait for service to go live!*/}
console.log("---------------------------Connected!---------------------------");
var response=await Register(base_url,(await b64_pubkey));
console.log(response?"---------------------------Registered---------------------------":"Something Went Wrong");
var {puzzle,stamp}=await FetchPuzzle(base_url,(await b64_pubkey))
console.log("---------------------------Puzzle---------------------------");
const solution=await secp.signAsync(await SHA256(JSON.stringify(puzzle)),(await privkey));
console.log("---------------------------Solve!---------------------------");
response=await SendSolution(base_url,puzzle,stamp,solution);
console.log(response?"---------------------------Verify!---------------------------":"Something Went Wrong");
})();

async function SHA256(message) {
  const hashBuffer = await crypto.subtle.digest("SHA-256", message); // hash the message
  const hashArray = Array.from(new Uint8Array(hashBuffer)); // convert buffer to byte array
  const hashHex = hashArray.map((b) => b.toString(16).padStart(2, "0")).join(""); // convert bytes to hex string
  return hashHex;
}

async function Connected(application) { try {
	return (await axios
	.get(`http://${application}/HeartBeat`))
	.data["msg"]==="alive";
} catch (error){ return false; } }

async function Register(application,key) { try {
	return (await axios
	.post(`http://${application}/RegisterKey`, {pubkey:key}))
	.data["msg"]==="success";
} catch (error){ return false; } }

async function FetchPuzzle(application,key){ try {
	return (await axios
	.get(`http://${application}/GenerateChallenge?identity=${key}`))
	.data
} catch (error){ return false; } }

async function SendSolution(application,puzzle,stamp,solution){ try {	
	return (await axios
	.post(`http://${application}/CheckSolution`, {puzzle:puzzle,stamp:stamp,solution:solution}))
	.data["msg"]==="success";
} catch (error){ return false; } }
