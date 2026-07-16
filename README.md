# Journal API

## Environment Variables

### App runtime (needed wherever the app runs, incl. AWS)

| Variable | Description |
| --- | --- |
`DB_MASTER_SECRET` | DB login credentials as JSON, e.g. `{"username":"admin","password":"hunter2"}`.
`DB_ENDPOINT` | The database hostname (DNS name), e.g. `journal-api-db.58138ad.us-east-1.rds.amazonaws.com`.
`DB_NAME` | The database name, e.g. `journal`.
`JWT_SECRET_KEY` | Secret key used to sign/verify login JWTs.
`DEFAULT_USER` | Username of the default app user created on startup.
`DEFAULT_USER_PASSWORD` | Password of the default app user created on startup.

### Local/CI build only

| Variable | Description 
`MYSQL_ROOT_PASSWORD` | Root password for the local MySQL container, read by the official `mysql` image's init script.
`MYSQL_DATABASE` | Database name created by the local MySQL container on first boot.
`DATABASE_URL` | Full SQLAlchemy DB connection string (e.g. `mysql+asyncmy://user:pass@mysql:3306/dbname`).
`DATABASE_URL_LOCAL` | Full SQLAlchemy DB connection string with localhost(e.g. `mysql+asyncmy://user:pass@localhost:3306/dbname`).
