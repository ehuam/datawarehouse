# PROJECT DESIGN NOTES:

This project uses a .env pattern to separate database configurations from the notebook.<br>

- A .env file is included and renamed ENV_PUBLIC to emphasis its public information. Normally this would be
ignored in a git repo and NEVER uploaded.
	- Should you want to replce it with your own values, you'll have to update the docker compose file.
      
- this project uses colima as the docker engine.

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

## HOW TO SHUTDOWN GRACEFULLY
1. Navigate to the project directory where docker compose file is located.
2. Stop the mongodb container:
```bash
docker compose stop
```
3. shutdown colima
```bash
colima stop
```

- confirm its shutdown
```bash
colima status
``` 
- should return "colima is not running"


### Dependencies
For this project we are using Firefox Web-Driver (geckodriver). <br>
Too avoid having user install binaries to their system, outside of python managed environment.<br>
We are using "webdriver-manager". 
