# Application Security & Privacy Architecture

**Standard**: Institutional Financial Security & Zero-Leakage AI Governance  
**Backend Security**: Spring Security 6 (Stateless JWT)  
**AI Security**: Air-Gapped Local Inference (Zero Data Exfiltration)  

---

## 1. Authentication & Authorization Architecture

- **Stateless JWT**: Authentication uses cryptographic JSON Web Tokens signed with HMAC-SHA256. Tokens are transmitted via the standard `Authorization: Bearer <token>` header.
- **Password Hashing**: User credentials are protected using `BCryptPasswordEncoder` with a cost factor of 10. Passwords are never stored in plaintext.
- **Resource Ownership Verification**: API endpoints enforce user membership checks (e.g., verifying that the calling user is an active member of `groupId` before allowing expense creation, settlement recording, or receipt uploads).

---

## 2. Air-Gapped Local AI Privacy Governance

A core architectural principle of Splitwise AI is complete data confidentiality:
- **Local Ollama Only**: AI inferences (receipt line items, spending trends, split interpretations) execute exclusively on the local machine at `http://127.0.0.1:11434`.
- **Zero Third-Party APIs**: No data, images, text, or metadata is ever transmitted to OpenAI, Claude, Google Cloud, or any external third-party API.
- **Air-Gap Capability**: Core financial workflows and local AI inference operate even when disconnected from the public internet.

---

## 3. Secure File Upload & Storage Pipeline

Physical receipt uploads adhere to strict defensive file-handling practices:
1. **Filename Sanitization**: Filenames are sanitized via `StringUtils.cleanPath()` to prevent directory traversal attacks (`../`).
2. **UUID Storage Partitioning**: Uploaded images are stored with randomized UUID filenames (`<uuid>.jpg`) in an isolated storage directory outside the web application context.
3. **MIME Type Whitelisting**: Only valid image media types (`image/jpeg`, `image/png`, `image/webp`) are accepted.
4. **Execution Prevention**: The uploads directory is not executable by the host web server.

---

## 4. Service-to-Service Boundary Protection

The AI Microservice communicates with the Spring Boot backend over an authenticated internal channel:
- **Header**: `X-Internal-Secret: <32-character-secret>`
- **Internal Protection**: FastAPI middleware verifies this token on every incoming request. Unauthorized calls receive an immediate `401 Unauthorized` response before executing any OCR or inference logic.

---

## 5. Input Validation & Financial Tamper Resistance

- **Integer Arithmetic & Range Guards**: Financial allocations are checked against negative amounts and zero values.
- **Reconciliation Check**: Custom and percentage splits are mathematically validated before persisting to the database.
- **SQL Injection Prevention**: All queries execute through Spring Data JPA Hibernate parameter bindings, preventing SQL injection vulnerabilities.
