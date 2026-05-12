# Patient App

A Flask-based web application for managing patient records with user authentication and admin functionality.

## Features

- User authentication (login/logout)
- Admin user registration
- Patient management (create, list, approve)
- File upload for patient attachments
- Audit logging
- Role-based access control

## Prerequisites

- Python 3.8+
- SQLite (default) or PostgreSQL/MySQL

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd patient_app
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate the virtual environment:

- Windows:
  ```bash
  .venv\Scripts\activate
  ```

- Linux/Mac:
  ```bash
  source .venv/bin/activate
  ```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up the database

Initialize the database and apply migrations:

```bash
flask --app run.py db init  # Only if migrations folder doesn't exist
flask --app run.py db migrate -m "Initial migration"
flask --app run.py db upgrade
```

### 5. Create an admin user

Run the admin creation script:

```bash
python create_admin.py
```

Follow the prompts to create an admin user.

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///database.db  # or your database URL
GOOGLE_API_KEY=your-google-api-key  # if using Google services
```

### Google API Configuration

If your app uses Google services (e.g., Google Maps, Google Drive):

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the required APIs (e.g., Maps API, Drive API)
4. Create credentials (API key)
5. Add the API key to your `.env` file as `GOOGLE_API_KEY`

## Running the Application

### Development Server

```bash
python run.py
```

The app will be available at `http://127.0.0.1:5001`

### Production Deployment

#### Using Gunicorn

1. Install Gunicorn:

```bash
pip install gunicorn
```

2. Run with Gunicorn:

```bash
gunicorn --bind 0.0.0.0:8000 --workers 4 run:create_app()
```

#### Using Nginx + Gunicorn

1. Install Nginx on your server.

2. Create a systemd service for Gunicorn:

Create `/etc/systemd/system/patient_app.service`:

```ini
[Unit]
Description=Patient App
After=network.target

[Service]
User=your-user
Group=your-group
WorkingDirectory=/path/to/patient_app
Environment="PATH=/path/to/patient_app/.venv/bin"
ExecStart=/path/to/patient_app/.venv/bin/gunicorn --bind unix:patient_app.sock -m 007 run:create_app
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Start and enable the service:

```bash
sudo systemctl start patient_app
sudo systemctl enable patient_app
```

4. Configure Nginx:

Create `/etc/nginx/sites-available/patient_app`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static {
        alias /path/to/patient_app/app/static;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/patient_app/patient_app.sock;
    }
}
```

5. Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/patient_app /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## Database Operations

### Export Database

To export the SQLite database:

```bash
sqlite3 database.db .dump > backup.sql
```

For other databases, use appropriate tools (e.g., pg_dump for PostgreSQL).

### Import Database

```bash
sqlite3 database.db < backup.sql
```

## Project Structure

```
patient_app/
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── patient/
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── static/
│   ├── templates/
│   └── utils.py
├── migrations/
├── config.py
├── run.py
├── requirements.txt
└── README.md
```

## API Endpoints

- `GET /` - Redirect to login
- `GET/POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET/POST /auth/register_admin` - Admin registration (admin only)
- `GET /patient/list` - List patients
- `GET/POST /patient/create` - Create new patient
- `POST /patient/<id>/approve` - Approve patient (admin only)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
