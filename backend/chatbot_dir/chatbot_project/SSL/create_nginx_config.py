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

    # Remove duplicate SSL parameters
    # ssl_protocols TLSv1.2 TLSv1.3;
    # ssl_prefer_server_ciphers on;
    # ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;

    # HSTS (optional, but recommended for security)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logs
    access_log /var/log/nginx/api-staging.mjproapps.com.access.log;
    error_log /var/log/nginx/api-staging.mjproapps.com.error.log;

    location / {
        proxy_pass http://127.0.0.1:8000;  # Assuming your Django app runs on port 8000
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files (adjust the path as needed)
    location /static/ {
        alias /path/to/your/static/files/;
    }

    # Media files (adjust the path as needed)
    location /media/ {
        alias /path/to/your/media/files/;
    }
}
    """

    nginx_path = "/etc/nginx/sites-available/api-staging.mjproapps.com"

    # Write the configuration to the file
    try:
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
