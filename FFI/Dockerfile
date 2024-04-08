FROM node:14
WORKDIR /app
COPY ./src/package*.json ./
RUN npm install
COPY ./src/ ./
RUN mkdir compiled-ff
RUN gcc -shared -o ./compiled-ff/library.so -fPIC exports.c
EXPOSE 3030
CMD [ "node", "--stack-size=104857600","./index.js" ]