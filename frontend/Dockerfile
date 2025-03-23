FROM node:16

WORKDIR /app

COPY package*.json ./

# Install dependencies with legacy peer deps flag to handle React 19
RUN npm install --legacy-peer-deps

COPY . .

EXPOSE 3000

CMD ["npm", "start"] 