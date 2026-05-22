# Legal ML: System Architecture & Workflow

Welcome to the internal documentation for **Legal ML**. This platform is a high-speed Enterprise Contract Auditor designed for transactional lawyers. It ingests unstructured contract PDFs, categorizes clauses, flags risks, and generates a formatted Microsoft Word audit report—all primarily leveraging local, lightweight ML models to ensure data privacy and near-instant execution.

Here is a step-by-step breakdown of how the entire system works in simple language.

---

## 1. The Frontend (The Cinematic UI)
**Tech Stack:** React 19, Vite, Tailwind CSS, GSAP, Supabase Auth

The frontend is designed to feel like a premium digital instrument ("Modern Trust" aesthetic). It utilizes high-end micro-interactions and smooth GSAP animations to hide loading times and provide a wow factor.
- **Supabase Authentication:** Users must log in via a secure authentication screen. This ensures their custom playbooks and data remain private to their specific `user_id`.
- **Playbook Management:** Users can upload their law firm's standard "Playbook" in `.txt` or `.pdf` formats. The frontend sends this file to the backend to be processed into JSON, and then instantly saves it to the user's Supabase account so it loads automatically on every future visit.
- **The Dashboard:** A drag-and-drop zone allows users to upload a contract (PDF or Image). Upon dropping the file, the UI displays a cinematic 6-step animation while communicating with the backend.

## 2. The API Layer (The Bridge)
**Tech Stack:** Python 3, FastAPI, Uvicorn

The backend is a robust FastAPI application serving as the bridge between the UI and the ML Pipeline. 
- **`/api/parse_playbook`:** Accepts unstructured playbooks (Text or PDF files). It extracts the raw text and runs it through the AI router model to categorize the firm's standard clauses, returning a clean JSON mapping.
- **`/api/analyze`:** The core endpoint. It receives the contract file along with the user's saved JSON Playbook. It saves the file temporarily and immediately hands it off to the `LegalDocumentAnalyzer` pipeline.
- **`/api/export`:** After analysis is complete, the frontend sends the raw JSON findings to this endpoint, which generates and returns a formatted `.docx` file.

## 3. The Machine Learning Pipeline (The Core Engine)
**Tech Stack:** `scikit-learn` (TF-IDF + LinearSVC), `pdfplumber`, `paddleocr`, Groq API

When a contract is handed to the `LegalDocumentAnalyzer`, it goes through a strict sequence of events:

### Step 1: Ingestion & OCR
- **PDF Extraction:** If the document is a native PDF, `pdfplumber` strips out formatting noise and cleanly extracts the text, carefully splitting it into individual paragraphs tied to their page numbers.
- **Image Extraction:** If the document is an image (or a scanned PDF), the pipeline automatically switches to `paddleocr` to read the text visually.

### Step 2: The SVM Router (Classification)
- **Lazy Loading:** The system entirely bypasses heavy Neural Networks. Instead, it lazily loads a pre-trained `scikit-learn` Support Vector Machine (`contract_svm_model.pkl`) and a TF-IDF Vectorizer. 
- **Categorization:** The Router model reads every single extracted paragraph and instantly categorizes it (e.g., assigning a paragraph to `PAYMENTS`, `GOVERNING LAW`, or `CONFIDENTIALITY`).

### Step 3: Playbook Deviation Engine
- Now that the contract is categorized, the system looks at the user's custom Playbook mapping.
- If the Router found a `PAYMENTS` clause in the contract, the Similarity Engine uses a lightning-fast TF-IDF comparison to see how similar it is to the `PAYMENTS` clause in the user's Playbook.
- If the text deviates significantly (e.g., less than 80% similarity), the pipeline flags it as a "Playbook Deviation".

### Step 4: Definitions Validator
- The engine uses complex Regex heuristics to hunt for "Defined Terms" (capitalized phrases like `"Confidential Information"`).
- It builds a dictionary of these terms and ensures they are actually defined somewhere in the text. If the contract uses a capitalized term but forgets to define it, the system flags it as an "Undefined Term" risk.

### Step 5: Fact Extraction (Groq LLM)
- While local ML does the heavy lifting for classification, the pipeline outsources specific factual questions to the cloud using the **Groq API** (`llama3-8b-8192`). 
- It asks targeted questions like *"When is payment due?"* based on the clauses it identified, returning precise answers to the user.

## 4. The Final Export
**Tech Stack:** `python-docx`
- Once the pipeline finishes, the results are sent back to the frontend.
- When the user clicks **"Export DOCX"**, the `/api/export` endpoint takes all the deviations, flagged risks, and undefined terms, and elegantly formats them into a Microsoft Word Document. 
- It adds an Executive Summary and calculates an overall Risk Posture (e.g., "Moderate" or "High") so the lawyer has a ready-to-use audit report!

## 5. Cybersecurity Hardening (Zero Trust)
To protect highly confidential corporate contracts, the architecture includes several strict security measures:
- **API Authentication:** All backend API endpoints are locked behind Supabase JWT validation. The frontend must send a valid `Bearer` token representing the authenticated user to access any services.
- **Strict CORS Enforcement:** The FastAPI backend strictly enforces Cross-Origin Resource Sharing (CORS), ensuring only the verified frontend origin can make requests.
- **Secure File Handling:** File uploads are limited to 10MB to prevent Denial of Service (DoS) attacks via resource exhaustion. The backend also utilizes Magic Byte validation (`filetype`) to ensure files are genuinely what they claim to be (e.g., a real PDF, not a disguised executable).
- **Air-Gapped / Strict Local Mode:** Because third-party cloud LLMs pose data privacy risks for legal documents, the UI offers an "Air-Gapped Mode" toggle. When enabled, the platform completely disables the cloud LLM connection (Groq API) and relies 100% on the local SVM and TF-IDF models.
- **Secure Ephemeral Storage:** Temporary files created during the pipeline are securely destroyed immediately after the extraction phase, ensuring no contract data lingers on the server disk.

## 6. Authentication & Database (Supabase)
**Tech Stack:** `supabase-js`, `supabase-py`, PostgreSQL
Supabase acts as the centralized Identity Provider and persistent storage layer for the platform. Its usage is critical for the "Zero Trust" architecture:
- **Frontend Session Management:** The React frontend utilizes `@supabase/supabase-js` to handle secure user authentication (login/registration) and maintain the user's active session.
- **Persistent Playbooks (Database):** When a user uploads a custom law firm playbook, the generated JSON mapping is saved directly into a Supabase PostgreSQL table (`playbooks`) and tied strictly to their `user_id`. This allows the user's custom standards to persist across sessions automatically.
- **Backend Authorization (JWT Verification):** The FastAPI backend uses the Supabase Python client (`supabase-py`) to intercept every incoming API request. It extracts the `Bearer` token sent by the frontend and verifies its cryptographic validity with the Supabase Auth server before allowing access to the machine learning pipeline.
