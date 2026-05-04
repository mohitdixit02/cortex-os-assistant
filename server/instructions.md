## Context
Total number of services: 3
1. cortex_server: backend server for assistant
2. cortex_queue: task queue for processing assistant tasks
3. cortex_core: langgraph worflows for execution

## Previous Setup
In earlier version, everything was in one repo. Task Queue start as asyncio loop. Backend voice_client submit the task to the queue and wait for the result. The core listen to queue, pick and execute the task and re-submit it to the queue. The backend listen to queue, pick result and return it to the frontend.

## New Setup
To make it more modular and scalable, we split the code into three separate services. 

## Your Task
## Task1: You to do the docker setup to start each service.
- cortex_server: uvicorn server running on port 8000
- cortex_queue: service that has endpoints exposed for adding task (by producer - cortex_server) and submitting task (consumer - cortex_core). It should submit tasks to a redis Queue, and cortex_core and cortex_server can both consume tasks from the redis Queue.
- cortex_core: service that listens to the redis Queue, pick and execute the task and submit the result back to the redis Queue.

## Task2:
As discussed above, you have to make services communicate using api endpoints. For this create sepaarte endpoints for each in new files.

### Instructions
- Implement the entry and exit logic as per new structure without touching any of the internal logic. Internal services logic is very sensitive and must not be changed.
- If any change required, create new files as much as possible and use older code as import, do not change the existing code.
- In the end, create a docker-compose file to start all three services together (other than redis and postgres).
- All the imports are done using absolute imports, so make sure to maintain the same structure for new files.
- Make sure that when service starts it is able to pick absoulte imports (specifically the cortex_cm which has commom modules, config, pg and redis clients)

## Redis DB Instructions
DB:0 - Use it for google tokens and verifier related service.
DB:1 - Use it for submitting tasks which will be listened by cortex_core.
DB:2 - Use it for submitting results which will be listened by cortex_server.

# Struct Instructions
Implement the changes in 3 services only. Prefer creating new files instead of changing existing files.
Dont change anything in the internal logic.
