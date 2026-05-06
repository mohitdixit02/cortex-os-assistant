## Project
This Project is cortex-os-assistant, a application that listens to the user queries in audio format, transcribes them to text, and then uses the langgraph worflows to generate the response. The response is then converted back to audio and played to the user. The project is designed to be a personal assistant that can help with various tasks such as setting reminders, answering questions, and providing information.

## Modules Overview
`app` - Contains the Electron + NextJS based application that serves as the user interface for the assistant. It handles audio recording, websocket communication, and playback of responses. It also involves the other endpoinst like tasks, history, profile and settings.

`cortex_event_tool` - Custom Event Tool which handles the user's reminders and events. It is an analogous to google task or calendar. It contains the endpoints to create and fetch the events created based on user and session.

`cortex_cm` - It contains the basic configuration, models utility, db setup and schemas for the project.
- `docs` - Table Schema (Just for reference, not used in code)
- `pg` - Contains the database setup and connection utilities, model schema, crud based operations, sql queries for postgres database.
- `redis` - Contains the redis client
- `utility` - Contains the utility functions for the project, model configurations used by langraph workflow, model initialization and other helper functions.

`cortex_core` - It contains the langgraph workflow which defines the logic for handling user queries, generating responses, and managing the conversation flow. It uses the utilities and models defined in `cortex_cm` to interact with the database and manage the state of the conversation.
- `graph` - Contains graphs workflows and states.
- `main` - Contains main_orchestration functions.
- `manager` - Contains the tool specific functions, and helper functions to execute tools.
- `memory` - Contains the memory management functions, and helper functions to manage the conversation history and context, saving and fetching memory and user info from postgres and redis database.
- `req.py` - Function to submit task once it is done.
- `worker.py` - Listens to redis db for new tasks.

`cortex_queue` - It contains the implementation of the task queue using Redis. Used to receiver new tasks, submit done tasks and manage the task status using redis. It has endpoints exposed which are used by other services.

`cortex_server` - It contains the FastAPI server implementation which exposes the endpoints for the application. It handles the incoming requests from the frontend using websocket as well as REST API (for history, profile, auth, etc.). 
- `controller` - contains multiple controllers for handling different endpoints like websocket, task, history, profile and settings.
- `cortex` - Includes sensory and voice_client models to transcribe audio and convert text to speech. voice_client generates the fallback response (for UX) and paralley submit the new task (if required) on the task queue.
- `services` - Contains the implementation of the services which are used by the controllers to handle the business logic of the application. Include stream, auth and basic endpoints based services.
- `services/stream` - Contains the implementation of the streaming response for the websocket endpoint, audio_bridge to sent audio in tokens and event driven streaming implementation.
- `server.py` - It is the entry point of the application which starts the FastAPI server and listens for incoming requests.

# Deployment
Refer to `docker-compose.yml` file for the deployment of the application. It includes the services for the server, worker, redis and postgres database.
