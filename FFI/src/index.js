const koffi = require('koffi');
const lib = koffi.load('./compiled-ff/library.so',{lazy: true});
const exponential_time = lib.func('int exponential_time(int ,int )');
const sum = lib.func('int sum(int ,int )');
const base = 2;
const exponent = 110;
function exponentialTimeExponentiation(base, exponent) {
    if (exponent === 0) {
        return 1;
    } else {
        return base * exponentialTimeExponentiation(base, exponent - 1);
    }
}
const test = 0;
if(test===1){
	console.time('Timer1');
	let result = exponential_time(base,exponent);
	console.log(`${base}^${exponent} = ${result}`);
	console.timeEnd('Timer1');
}
else{
	console.time('Timer2');
	result = exponentialTimeExponentiation(base, exponent);
	console.log(`${base}^${exponent} = ${result}`);
	console.timeEnd('Timer2');
}