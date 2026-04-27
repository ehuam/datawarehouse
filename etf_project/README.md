# PROJECT DESIGN NOTES:

This project uses a .env pattern to separate database configurations from the notebook.<br>

- A .env file is included and renamed ENV_PUBLIC to emphasis its public information. Normally this would be
ignored in a git repo and NEVER uploaded.
	- Should you want to replce it with your own values, you'll have to update the docker compose file.

## HOW TO RUN
1. Start your docker engine - if using docker desktop: make sure the application is open.
 - if using COLIMA: run colima start --cpu 2 --memory 4

2. Initialize the database
- run the following
```bash
docker compose --env-file ENV_PUBLIC up -d 
```
3. Run the notebook:
- The notebook is configured to connect to the database using the ENV_PUBLIC variables. If you have changed the .env file, make sure to update the notebook connection string accordingly.