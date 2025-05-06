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
easiest way is to load the postman collection in tests/ folder and run each request

medium way is to do it via the http://localhost:8000/docs endpoint

hard way is raw curl:
GET /health: ```curl --location 'http://localhost:8000/health'```

GET /documents: ```curl --location 'http://localhost:8000/documents'```

POST /documents: 
```
curl --location 'http://localhost:8000/documents' \
--header 'Content-Type: application/json' \
--data '{
    "title": "Soap note 1",
    "content": "SOAP Note - Encounter Date: 2023-10-26\r\nPatient: patient--001\r\n\r\nS: Pt presents today for annual physical check-up. No chief complaints. Reports generally good health, denies chest pain, SOB, HA, dizziness. Family hx of elevated cholesterol (dad), no significant personal PMH issues reported. States routine exercise (~2x\/wk), balanced diet but with occasional fast-food. Denies tobacco use, reports occasional ETOH socially.\r\n\r\nO:\r\nVitals:\r\n\r\nBP: 128\/82 mmHg\r\nHR: 72 bpm, regular\r\nRR: 16 breaths\/min\r\nTemp: 98.2\u00C2\u00B0F oral\r\nHt: 5'\''10\", Wt: 192 lbs, BMI: 27.5 (overweight)\r\nGeneral appearance: Alert, NAD, pleasant and cooperative.\r\nSkin: Clear, normal moisture\/turgor\r\nHEENT: PERRLA, EOMI, no scleral icterus. Oral mucosa moist, throat clear, no erythema\r\nCV: Regular rate & rhythm, no murmurs, rubs or gallops\r\nLungs: CTA bilaterally, no wheezing or crackles\r\nABD: Soft, NT\/ND, bowel sounds normal\r\nNeuro: CN II-XII intact, normal strength & sensation bilat\r\nEXT: No edema, pulses +2 bilaterally\r\nLabs ordered: CBC, CMP, Lipid panel\r\n\r\nA:\r\n\r\nAdult annual health exam, generally healthy\r\nPossible overweight (BMI 27.5), recommend lifestyle modifications\r\nFamily hx of hyperlipidemia, screening initiated\r\nP:\r\n\r\nAdvised pt on healthier diet, increasing weekly exercise frequency to at least 3-4 times\/week\r\nScheduled follow-up visit to review lab results and cholesterol levels in approx. 5 months\r\nRoutine annual influenza vaccine administered today - tolerated well\r\nNo Rx prescribed at this visit.\r\n\r\nSigned:\r\nDr. Mark Reynolds, MD\r\nInternal Medicine"
}'
```

POST /answer_question 
```
curl --location 'http://localhost:8000/answer_question' \
--header 'Content-Type: application/json' \
--data '{
    "question": "What lab work should patient--001 get?"
}'
```

POST /summarize_note
```
curl --location 'http://localhost:8000/summarize_note' \
--header 'Content-Type: application/json' \
--data '{
    "content": "SOAP Note - Encounter Date: 2023-10-26\r\nPatient: patient--001\r\n\r\nS: Pt presents today for annual physical check-up. No chief complaints. Reports generally good health, denies chest pain, SOB, HA, dizziness. Family hx of elevated cholesterol (dad), no significant personal PMH issues reported. States routine exercise (~2x\/wk), balanced diet but with occasional fast-food. Denies tobacco use, reports occasional ETOH socially.\r\n\r\nO:\r\nVitals:\r\n\r\nBP: 128\/82 mmHg\r\nHR: 72 bpm, regular\r\nRR: 16 breaths\/min\r\nTemp: 98.2\u00C2\u00B0F oral\r\nHt: 5'\''10\", Wt: 192 lbs, BMI: 27.5 (overweight)\r\nGeneral appearance: Alert, NAD, pleasant and cooperative.\r\nSkin: Clear, normal moisture\/turgor\r\nHEENT: PERRLA, EOMI, no scleral icterus. Oral mucosa moist, throat clear, no erythema\r\nCV: Regular rate & rhythm, no murmurs, rubs or gallops\r\nLungs: CTA bilaterally, no wheezing or crackles\r\nABD: Soft, NT\/ND, bowel sounds normal\r\nNeuro: CN II-XII intact, normal strength & sensation bilat\r\nEXT: No edema, pulses +2 bilaterally\r\nLabs ordered: CBC, CMP, Lipid panel\r\n\r\nA:\r\n\r\nAdult annual health exam, generally healthy\r\nPossible overweight (BMI 27.5), recommend lifestyle modifications\r\nFamily hx of hyperlipidemia, screening initiated\r\nP:\r\n\r\nAdvised pt on healthier diet, increasing weekly exercise frequency to at least 3-4 times\/week\r\nScheduled follow-up visit to review lab results and cholesterol levels in approx. 5 months\r\nRoutine annual influenza vaccine administered today - tolerated well\r\nNo Rx prescribed at this visit.\r\n\r\nSigned:\r\nDr. Mark Reynolds, MD\r\nInternal Medicine"
}'
```

POST /extract_structured
```
curl --location 'http://localhost:8000/extract_structured' \
--header 'Content-Type: application/json' \
--data '{
    "raw_note": "SOAP Note - Encounter Date: 2024-03-15 (Follow-Up Visit)\r\nPatient: patient--001\r\nS: Pt returns for follow-up on cholesterol, as planned in prior physical. Labs drawn on previous encounter indicating elevated LDL (165 mg\/dL), mildly reduced HDL (38 mg\/dL), triglycerides at upper normal limits (145 mg\/dL). Pt admits difficulty adhering strictly to suggested dietary changes, but did slightly increase physical activity. Denies chest discomfort, palpitations, SOB, orthopnea, or PND.\r\n\r\nO:\r\nVitals today:\r\n\r\nBP: 134\/84 mmHg\r\nHR: 78 bpm\r\nWeight stable at 192 lbs\r\nPhysical Exam unchanged from last assessment, no new findings.\r\n\r\nReview of labs (drawn on 2023-10-26):\r\n\r\nLDL cholesterol elevated at 165 mg\/dL (desirable <100 mg\/dL)\r\nHDL low at 38 mg\/dL (desired >40 mg\/dL)\r\nTriglycerides borderline at 145 mg\/dL (normal <150 mg\/dL)\r\nNo indications of DM, liver or kidney dysfunction observed on CMP results.\r\n\r\nA:\r\n\r\nHyperlipidemia\r\nOverweight status, decreased HDL\r\nStable vitals, no acute distress or cardiovascular symptoms\r\nP:\r\n\r\nInitiate atorvastatin 20 mg PO daily qHS; discussed risks\/benefits with pt\r\nPt advised again regarding diet and lifestyle modifications\r\nRecommend continued aerobic exercise (at least 4 sessions\/week, moderate intensity, 30-40 mins per session)\r\nRepeat lipid panel, LFTs after 3 months of statin therapy initiation\r\nReturn for follow-up in 3 months or earlier if any adverse reaction occurs.\r\nPrescription Note:\r\n\r\nAtorvastatin 20mg tab Disp: #90 (ninety) tabs Sig: 1 tablet PO daily at bedtime Refills: 3\r\nSigned:\r\nDr. Mark Reynolds, MD\r\nInternal Medicine"
}'
```

POST /to_fhir
```
curl --location 'http://localhost:8000/to_fhir' \
--header 'Content-Type: application/json' \
--data '{ "structured_note": {"created_at":null,"patient":{"first_name":null,"last_name":null,"dob":null,"id":"patient--001","gender":null},"conditions":[{"type":"Condition","raw_text":"difficulty adhering strictly to suggested dietary changes","name":"Patient'\''s noncompliance with dietary regimen","code":"Z91.11","system":"ICD"}],"diagnoses":[{"type":"Diagnosis","raw_text":"Hyperlipidemia","name":"Mixed hyperlipidemia","code":"E78.2","system":"ICD"},{"type":"Diagnosis","raw_text":"Overweight status, decreased HDL","name":"Overweight and obesity","code":"E66","system":"ICD"}],"treatments":[{"type":"Treatment","raw_text":"slightly increase physical activity","name":"Activity, physical games generally associated with school recess, summer camp and children","code":"Y93.6A","system":"ICD"},{"type":"Treatment","raw_text":"discussed risks/benefits with pt","name":"Open angle with borderline findings, low risk","code":"H40.01","system":"ICD"},{"type":"Treatment","raw_text":"Pt advised again regarding diet and lifestyle modifications","name":"Defects in post-translational modification of lysosomal enzymes","code":"E77.0","system":"ICD"},{"type":"Treatment","raw_text":"Recommend continued aerobic exercise (at least 4 sessions/week, moderate intensity, 30-40 mins per session)","name":"Activity, aerobic and step exercise","code":"Y93.A3","system":"ICD"}],"medications":[{"type":"Medication","raw_text":"Initiate atorvastatin 20 mg PO daily qHS","name":"ATORVASTATIN","code":"83367","system":"RXNORM"},{"type":"Medication","raw_text":"Atorvastatin 20mg tab Disp: #90 (ninety) tabs Sig: 1 tablet PO daily at bedtime Refills: 3","name":"ATORVASTATIN","code":"83367","system":"RXNORM"}],"observations":[{"type":"Observation","raw_text":"elevated LDL (165 mg/dL)","name":null,"code":null,"system":null},{"type":"Observation","raw_text":"mildly reduced HDL (38 mg/dL)","name":"Disorders of bile acid and cholesterol metabolism","code":"E78.7","system":"ICD"},{"type":"Observation","raw_text":"triglycerides at upper normal limits (145 mg/dL)","name":null,"code":null,"system":null},{"type":"Observation","raw_text":"Denies chest discomfort, palpitations, SOB, orthopnea, or PND","name":null,"code":null,"system":null},{"type":"Observation","raw_text":"BP: 134/84 mmHg","name":null,"code":null,"system":null},{"type":"Observation","raw_text":"HR: 78 bpm","name":null,"code":null,"system":null},{"type":"Observation","raw_text":"Weight stable at 192 lbs","name":null,"code":null,"system":null},{"type":"Observation","raw_text":"Physical Exam unchanged from last assessment, no new findings","name":null,"code":null,"system":null},{"type":"Observation","raw_text":"LDL cholesterol elevated at 165 mg/dL (desirable <100 mg/dL)","name":null,"code":null,"system":null},{"type":"Observation","raw_text":"HDL low at 38 mg/dL (desired >40 mg/dL)","name":null,"code":null,"system":null},{"type":"Observation","raw_text":"Triglycerides borderline at 145 mg/dL (normal <150 mg/dL)","name":null,"code":null,"system":null},{"type":"Observation","raw_text":"No indications of DM, liver or kidney dysfunction observed on CMP results","name":null,"code":null,"system":null},{"type":"Observation","raw_text":"Stable vitals, no acute distress or cardiovascular symptoms","name":null,"code":null,"system":null}],"plan_actions":[{"type":"PlanAction","raw_text":"Repeat lipid panel, LFTs after 3 months of statin therapy initiation","name":"Abnormal results of liver function studies","code":"R94.5","system":"ICD"},{"type":"PlanAction","raw_text":"Return for follow-up in 3 months or earlier if any adverse reaction occurs","name":null,"code":null,"system":null}]}}'
```



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

