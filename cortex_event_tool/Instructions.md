## Context
Refer to `context/project.md` for the overview of the project, its modules and how it works. At current stage, `cortex_event_tool` is not ready. It is a custom tool (an analogy to google calendar or task) which will handle the user's reminders and events. You have to implement the tool by following below steps:

## DB Setup
1. Create a new table for event_tool in pg.
```sql
-- 1. ENUMS
CREATE TYPE event_status AS ENUM ('CREATED', 'QUEUED', 'DONE', 'FAILED', 'CANCELLED');

-- 2. USER_EVENTS TABLE (The Scheduler)
-- Stores the specific data for things the AI must do in the future.
CREATE TABLE user_events (
    id UUID PRIMARY KEY DEFAULT,
    user_id UUID NOT NULL,
    session_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    event_info TEXT,
    event_description TEXT,
    embedding VECTOR,
    trigger_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status event_status DEFAULT 'CREATED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. PERFORMANCE INDEXES
CREATE INDEX idx_events_trigger_time ON user_events(trigger_time) WHERE status = 'CREATED';
```
Validate above schema, and check if its right or not. accordingly update the `create_tables.sql` file in `cortex_cm/pg` module. I will execute the sql file later. Also update the `docs/TABLE_SCHEMA.md` file with the new table schema for reference.

2. Create the corresponding enums and models in the `cortex_cm/pg` module.
3. Do the same for redis, create a new file `cortex_cm/redis/event_tool.py` and create the logic to save the events in redis with the key pattern `event_tool:{event_id}:{event_trigger_time}`. Also create the logic to fetch the events based on the key pattern.
4. Update the `tasks` table and add column task_owner, which has enum (VOICE_CLIENT, EVENT_TOOL, OTHER). This will help us to identify which module has created the task and accordingly we can decide the flow in the task queue. Update the `create_tables.sql` file in `cortex_cm/pg` module and also update the `docs/TABLE_SCHEMA.md` file with the new table schema for reference.

## cortex_event_tool Module
1. Create the main file for the tool `cortex_event_tool/main.py` which will include the logic to create a new event, fetch the events based on user and session, and also the logic to check for the events which are due and logic to update the event status. Events should be saved in PG, but also in Redis, so that worker can listen to them.
2. Create a `cortex_event_tool/req.py` file which will include endpoints for the above logic, and other services will use this endpoint.
3. Create a worker file `cortex_event_tool/worker.py` which will run a loop to check for the events which are due and submit them to the task queue. You can use the existing `cortex_queue` `add_task` method to submit the tasks.
4. New events are queued in `redis_db:4` with the key pattern `event_tool:{event_id}:{event_trigger_time}`. The worker will listen to these keys and process the events accordingly.
5. If (event_trigger_time - current_time) is less than or equal to 5 mins, the worker will submit the task to the task queue.

## Integration with task_queue
1. `cortex_queue/main.py` file must be used for implementation. add_task function has metadata key, make sure to add key_value pair = `task_type: tool_execution`. Task Queue will move the task to redis pending task queue, without following any saving route, if task_type is tool_execution.
2. New task will be added with TASK_OWNER as EVENT_TOOL, for task_type: `query`, TASK_OWNER will be VOICE_CLIENT.
3. Once added to pending queue, cortex_queue will request the cortex_event_tool update status endpoint to update the status of the event to QUEUED.
4. Similarly once the cortex_core do the submission, task_queue will request the cortex_event_tool update status endpoint to update the status of the event to DONE or FAILED based on the response from cortex_core.

## Integration with cortex_core
1. `cortex_core/manager/tools.py` file has other tools implemented, you can refer to them for the implementation of event_tool.
2. Create a new function in the tools.py file for event_tool. It will be called by workflow (you dont have to worry about that, make sure that description of the tool is clear and it should be clear from the function name that what it does). This function will call the `cortex_event_tool/req.py` endpoint to create a new event, and a function to fetch the event. Fetching should be done in 3 modes, refer to task_tool implementation for it.
3. In the end, make sure that main_workflow only pick tasks whose task_owner is VOICE_CLIENT. For event_tool task, I will make workflow separetley. Task_type is used internally by task_queue  and provided by event_tool or voice_client, cortex_core must only see TASK_OWNER, which is also the column of the Task Table.

## Instructions
1. Make sure to refer the project structure first to understand what you are building.
2. write functions with proper input and return type, and also add docstrings to the functions for better understanding. Refer `cortex_server/service/stream for understanding the docstring format.
3. Make sure to write modular code, and avoid writing large functions. If you find that a function is doing multiple things, try to break it down into smaller functions.
4. Make sure to handle exceptions properly and return appropriate error messages.
