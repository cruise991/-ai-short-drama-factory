FROM nginx:alpine

COPY dist /usr/share/nginx/html
# Copy custom nginx configuration with reverse proxy and large upload support
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

