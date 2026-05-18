# Architecture in Voice Streaming Flow
### Objective: Handling the conversation gap or natuarallly occurring silence or pause the conversation flow.

### Context
Currently when `UserSpeechEndEvent` is received from the UI, system assumes that the user has finished speaking and it start processing audio.

### Implementation Steps
1. A separate class or function is required, as soon as `UserSpeechEndEvent` is received, instead of directly processing the audio, it will transition to a new state called `WAITING_FOR_FURTHER_AUDIO`.
2. The current audio buffer will be transcribed and processed and stored in a set of strings.
3. This set of strings will be pased to LLM, to decide the confidence score that whether user has finished his conversation or not. If confidence score is above threshold, then it will emit the event `FINISH_LISTENING` and start processing the audio, otherwise it will wait for further audio input from the user.
4. While waiting for further audio input, there will be a `WAIT_FOR_AUDIO_TIMEOUT` timer, if the timer expires without receiving any further audio input, it will emit the event `FINISH_LISTENING` and start processing the
audio.

### Task
1. You have to implement the above architecture in the voice streaming flow.
2. Implement the `WAITING_FOR_FURTHER_AUDIO` key in the StreamEvent Map.
3. For the current websocket logic, taking audio snapshot and processing it is correct. It will change inside `startStreamResponse` function, and stream client's `stream_response` function.
4. Implement the logic to keep collecting transcribed audio in a set of strings and pass it to LLM for confidence score calculation.
5. Implement the logic to handle `WAIT_FOR_AUDIO_TIMEOUT` timer and emit `FINISH_LISTENING` event if timer expires without receiving further audio input.
6. Rest of the flow will remain the same. Prefer to write LLM based functions in the voice client.
