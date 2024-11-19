import os

def create_nginx_config():
    config = """
server {
    listen 80;
    server_name api-staging.mjproapps.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name api-staging.mjproapps.com;

    ssl_certificate /etc/letsencrypt/live/api-staging.mjproapps.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api-staging.mjproapps.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Logs
    access_log /var/log/nginx/api-staging.mjproapps.com.access.log;
    error_log /var/log/nginx/api-staging.mjproapps.com.error.log;

    location / {
        # CORS headers
        add_header 'Access-Control-Allow-Origin' 'https://staging.mjproapps.com' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;


        # Proxy settings
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_buffering off;
        proxy_redirect off;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;

        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' 'https://staging.mjproapps.com' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain charset=UTF-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }
}
    """

    # Define the path for the Nginx configuration file
    nginx_path = "/etc/nginx/sites-available/api-staging.mjproapps.com"

    try:
        # Write the configuration to the file
        with open(nginx_path, "w") as f:
            f.write(config)
        print(f"Nginx configuration file created at {nginx_path}")

        # Create a symbolic link in sites-enabled
        symlink_path = "/etc/nginx/sites-enabled/api-staging.mjproapps.com"
        if not os.path.exists(symlink_path):
            os.symlink(nginx_path, symlink_path)
            print(f"Symbolic link created at {symlink_path}")
        else:
            print(f"Symbolic link already exists at {symlink_path}")

        print("Configuration complete. Remember to test and reload Nginx.")
    except PermissionError:
        print("Error: Permission denied. Try running the script with sudo.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    create_nginx_config()