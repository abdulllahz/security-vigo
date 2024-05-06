const postgres = require('@pg');
const { constants } = postgres;
const { BinaryInt, VarChar } = constants;
const maxQuery = 500;
const maxRows = 10000;
const getCount = (queries) => {
    return Math.min(parseInt((queries) || 1, 10), maxQuery) || 1;
}
const sprayer = (max = 100) => {
    const ar = [0]
    for (let i = 0; i < max; i++) {
      ar[i + 1] = (new Array(i + 1)).fill(1)
    }
    max += 1
    return (n, fn) => ar[n % max].map(fn)
}
const getRandom = () => Math.ceil(Math.random() * maxRows);
const getWorldById = await pg.compile({
    portal: '',
    formats: [#:TYPES],
    name: 'worlds',
    maxRows: 0,
    params: [0],
    sql: 'SELECT #:KCOLUMNS: FROM world WHERE column0 = $1',
    fields: [
      #:KCOLUMNTYPES
      //{ format: BinaryInt, name: 'id' },
      //{ format: BinaryInt, name: 'randomnumber' }
    ]
})
const getRandomWorld = () => getWorldById(getRandom())
const spray = sprayer(maxQuery);
for (let i = 0; i < max; i++) {
    console.log(await Promise.all(spray(getCount(N), getRandomWorld)));
}