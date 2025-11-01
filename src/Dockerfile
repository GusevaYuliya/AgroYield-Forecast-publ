FROM node:22-bookworm

WORKDIR /app

# Копирование package.json и установка зависимостей
COPY ../package*.json ./
RUN npm install

# Копирование исходного кода
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]