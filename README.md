# Installation

```
git clone https://github.com/cubesnyc/ascertain.git
cd ascertain

touch backend/.env
echo "OPENAI_API_KEY=..." >> backend/.env
echo "OPENAI_MAX_TOKENS_MIN=..." >> backend.env   # optional. if you have higher limits than 200k tokens per minute

docker-compose up --build -d
```
# API
swagger API: http://localhost:8000/docs

# Testing
postman collection in tests/ folder

# Notes
### Vector Store
PGVector was used as the vector store

### Embeddings
When a document is POSTed it is stored in a CHUNK_PENDING state. A queue worker reads documents off of this queue and processes them.

400 token blocks with minor over lap are used to generate the chunks. After these naive chunks are formed, they are hydrated with context to make them contextually aware.
This seemed like the safest robust approach not knowing the full scope of documents that would be added. For large documents this can take some time. 

### RAG
When queried, a query is expanded into multiple variants. Each variant is then queried against our vector store and the top-10 are chosen using cosine distance. 
If chunks are cited in the answer they will be included with the response. 

### Structured Note Extraction
The structured note extraction is purposely roundabout. We first extract medical concepts from the note to form a batch of concepts. Each batch of concepts then launches
an agent that determines which API tool (ICD, RXNorm, None) to call for that concept. The appropriate API is then called to retrieve the code. The concept is hydrated with the code.
The fully hydrated list of concepts is then fed into the LLM again in the final step to produce the structured note. 

### FIHR
fhir.resources is used to map the structured note concepts to FHIR standard.

