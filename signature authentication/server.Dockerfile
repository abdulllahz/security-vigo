FROM node:16
WORKDIR /home
COPY package.json package.json
RUN npm install
COPY . .
EXPOSE 3000
CMD [ "node", "index.js" ]