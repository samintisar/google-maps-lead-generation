# Use Node.js 20 Alpine for smaller image size
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install all dependencies (including devDependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port 5173 for development
EXPOSE 5173

# For development, start dev server with host binding
# For production, you would use npm run preview or a production server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"] 