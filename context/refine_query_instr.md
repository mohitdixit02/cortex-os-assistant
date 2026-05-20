## Context
`conversation_gap_handling_architecture.md` has information on how the query get refined in the case, user has something like "forget this" or "ignore this" in the conversation.

## Current Flow
Refined query becomes the actual query and is passed to the further flow, which leads to the loss of the original query. This is not ideal as the original query may have some important information which is not present in the refined query.

## Implementation
We will still pass the refined query to the further flow. But we will save the original query in the database. Implement following:
1. Add new fields:
- `is_refined_query` (boolean): to indicate whether the query is refined or not.
- `refined_query` (string): to store the refined query if it is refined.
2. When a query is refined, set `is_refined_query` to true and store the refined query in `refined_query` field. The original query will still be stored in the `query` field.
3. In the further flow, refined query will be used (existing flow is already have the same).
4. In the UI, both refined and original query will be shown to the user. The original query will be shown as "Original Query: <original_query>" and the refined query will be shown as "Refined Query: <refined_query>". If the query is not refined, only the original query will be shown. It will give better UX.
