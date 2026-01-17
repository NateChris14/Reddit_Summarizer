# Using an nginx base image
FROM nginx:alpine

# Removing the default nginx static files
RUN rm -rf /usr/share/nginx/html/*

# Copying the frontend files into Nginx's static directory
COPY . /usr/share/nginx/html

# Exposing port 80
EXPOSE 80

# Starting nginx
CMD ["nginx", "-g", "daemon off;"]