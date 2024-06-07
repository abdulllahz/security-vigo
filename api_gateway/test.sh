#/bin/bash
#Creds
#Preprod_Administrator:_Naltrexone*747
# http://34.240.77.7:1337:AmmarEjaz:8CYJeuPk4ZRS
# http://34.240.77.7:1337:ViperRafay:3QcNnI7w4vw
# http://34.240.77.7:1337:AliBhai:3QcNnuPk4ZRS
# http://34.240.77.7:1337:AUBhai:SRZ4kPunNcQ3
# http://34.240.77.7:1337:Anas:SRZ4kPueJYC8
# http://34.240.77.7:1337:hsf:OpTp123
echo '==========================================================='
echo 'Starting DB'
echo '==========================================================='
docker run -d --rm --name kong-database \
-e "POSTGRES_USER=kong" \
-e "POSTGRES_DB=kong" \
-e "POSTGRES_PASSWORD=kong" \
-p 5432:5432 \
postgres:9.6.24-alpine
#postgres:16.0-alpine3.18
sleep 10

echo '==========================================================='
echo 'Running Migrations'
echo '==========================================================='
docker run --rm --link kong-database:kong-database pantsel/konga:0.14.9 \
-c prepare \
-a postgres \
-u postgresql://kong:kong@kong-database:5432/postgres
docker run -d --rm \
--link kong-database:kong-database \
-e "KONG_DATABASE=postgres" \
-e "KONG_PG_HOST=kong-database" \
-e "KONG_PG_USER=kong" \
-e "KONG_PG_PASSWORD=kong" \
-e "KONG_CASSANDRA_CONTACT_POINTS=kong-database" \
kong:3.4 kong migrations bootstrap
sleep 10

echo '==========================================================='
echo 'Starting Services'
echo '==========================================================='
docker run -d --rm --name kong-gateway \
--link kong-database:kong-database \
-e "KONG_DATABASE=postgres" \
-e "KONG_PG_HOST=kong-database" \
-e "KONG_PG_PASSWORD=kong" \
-e "KONG_CASSANDRA_CONTACT_POINTS=kong-database" \
-e "KONG_PROXY_ACCESS_LOG=/dev/stdout" \
-e "KONG_ADMIN_ACCESS_LOG=/dev/stdout" \
-e "KONG_PROXY_ERROR_LOG=/dev/stderr" \
-e "KONG_ADMIN_ERROR_LOG=/dev/stderr" \
-e "KONG_ADMIN_LISTEN=0.0.0.0:8001, 0.0.0.0:8444 ssl" \
-p 8000:8000 \
-p 8443:8443 \
-p 8001:8001 \
-p 8444:8444 \
kong:3.4
docker run -d --rm --name kong-konga \
--link kong-database:kong-database \
--link kong-gateway:kong-gateway \
-e "TOKEN_SECRET=MYSECRET" \
-e "DB_ADAPTER=postgres" \
-e "DB_URI=postgresql://kong:kong@kong-database:5432/postgres" \
-e "NODE_ENV=production" \
-p 1337:1337 \
pantsel/konga:0.14.9