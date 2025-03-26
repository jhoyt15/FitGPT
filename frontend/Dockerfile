FROM node:16

WORKDIR /app

RUN npm install firebase

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"] 