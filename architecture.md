# GSA Document Analyzer - Architecture

## Overview

The system ingests vendor documents, parses and redacts PII, validates compliance, and uses AI (RAG + LLM) for advanced analysis and communication generation.

---

## Data Flow Diagram

```
+-------------------+
|   User Uploads    |
|   Documents (UI)  |
+-------------------+
          |
          v
+-----------------------+
|   /api/ingest_v2      |  <-- FastAPI endpoint
+-----------------------+
          |
          v
+-----------------------+
| Document Classifier   |---+
+-----------------------+   |
          |                (splits by doc type)
          v                 |
+-----------------------+   |
|  Document Parsers     |<--+
| (Profile, Past Perf,  |
|  Pricing)             |
+-----------------------+
          |
          v
+-----------------------+
|   PII Redactor        |
+-----------------------+
          |
          v
+-----------------------+
| In-Memory Store       |  <-- Stores redacted & parsed data by request_id
+-----------------------+
          |
          v
+-----------------------+
|   /api/analyze        |  <-- FastAPI endpoint
+-----------------------+
          |
          v
+-----------------------+
|  Validator Service    |---+
+-----------------------+   |
          |                |
          v                |
+-----------------------+   |
|   RAG Service         |---+---+
| (GSA Rules Index)     |       |
+-----------------------+       |
          |                    |
          v                    |
+-----------------------+      |
|   LLM Service         |<-----+
| (Gemini 2.0 Flash)    |
+-----------------------+
          |
          v
+-----------------------+
|   Results (UI/API)    |
+-----------------------+
```

---

## Component Diagram

```
+-------------------+
|   FastAPI App     |
+-------------------+
        |
        v
+-------------------+      +-------------------+
|   Routers         |----->|  Services         |
| (ingest, analyze) |      | (parser, rag, llm)|
+-------------------+      +-------------------+
        |                          |
        v                          v
+-------------------+      +-------------------+
|  Document Store   |      |  AI/ML Models     |
|  (in-memory)      |      | (Gemini, RAG)     |
+-------------------+      +-------------------+
```

---

## Where AI is Used

- **RAG Service**: Retrieves relevant GSA rules using semantic search (sentence-transformers + ChromaDB).
- **LLM Service**: Uses Google Gemini 2.0 Flash to generate:
  - Negotiation briefs for internal GSA use.
  - Professional client emails for vendors.
  - JSON checklists for compliance issues.

# Architecture & Scalability

This document outlines the architectural principles of the GSA Document Analyzer, focusing on its ability to scale from a prototype to a large-scale production system and its flexibility for future feature development.

---

## 🚀 Core Architectural Principles

Our design philosophy is built on modern software engineering best practices to ensure the system is robust, maintainable, and ready for growth.

### 1. Stateless API Layer
The FastAPI backend is **stateless**, meaning each API request is independent and contains all the information needed to be processed. This is crucial for scalability, as it allows us to run multiple copies of the API server behind a load balancer without worrying about session synchronization.

### 2. Separation of Concerns (SoC)
The system is broken down into logical, independent components:
- **Parsing**: Extracts data from raw text
- **Validation**: Checks data against deterministic business rules
- **RAG (Retrieval)**: Fetches relevant context from a vector store
- **LLM (Generation)**: Creates human-readable analysis and communication

This modularity allows each component to be developed, tested, and scaled independently.

### 3. Asynchronous-First Design
By using FastAPI, the system is built to handle asynchronous operations. This is the foundation for moving long-running tasks (like AI analysis) to background workers, ensuring the API remains fast and responsive.

### 4. Centralized Configuration
Key settings (like API keys and model names) are managed through environment variables, not hardcoded. This allows us to reconfigure the system for different environments (development, staging, production) without changing the code.

---

## 📈 The Path to 1,000 Customers: A Scalability Roadmap

The architecture is designed to evolve gracefully as user load increases.

### Phase 1: Prototype (1-10 Users)

**Architecture**: A single, synchronous FastAPI server holds all data in memory (`document_store` dictionary).

**How it Works**: The user sends a request, the server processes it from start to finish, and then sends a response.

**Limitation**: Simple and fast for one user, but processing time increases with more users, and all data is lost if the server restarts.

```
User → FastAPI Server (Sync Processing + In-Memory Storage)
```

### Phase 2: Growth (10-100s of Users)

To handle hundreds of concurrent users, we introduce asynchronous processing and persistent storage.

**Architecture**:
1. A **Load Balancer** distributes incoming requests across multiple FastAPI servers
2. The `ingest` endpoint immediately places a new job onto a **Message Queue** (like Redis or RabbitMQ)
3. A pool of **Background Workers** (e.g., Celery) picks up jobs from the queue to perform the heavy lifting (parsing, validation, AI analysis)
4. The in-memory `document_store` is replaced with a **Persistent Database** (like PostgreSQL or MongoDB) and a dedicated **Vector Store**

**Benefit**: The API responds instantly, and the system can handle bursts of traffic by queuing jobs. The database ensures data is safe and durable.

```
User → Load Balancer → [API Server] [API Server] → Message Queue → [Worker] [Worker] → Database & Vector Store
```

### Phase 3: Scale (1,000+ Users)

To support thousands of users, we evolve from a single application to a distributed system of microservices.

**Architecture**: The application is broken down into independent **Microservices**, each running in its own container (e.g., Docker) and managed by an orchestrator (e.g., Kubernetes).

- **Ingestion Service**: Handles document uploads and PII redaction
- **Analysis Service**: Runs validation, RAG, and LLM logic  
- **Notification Service**: Manages sending emails

**Benefit**: Each service can be scaled independently based on its specific load. For example, if AI analysis is slow, we can add more `Analysis Service` containers without touching the rest of the system. This provides maximum efficiency, resilience, and maintainability at scale.

```
User → API Gateway → [Ingestion Service] [Analysis Service] [Notification Service] → ...
```

---

## 🔧 Evolving the System: Adding "Pricing Pack v2"

A key strength of this architecture is its extensibility. Here's how we can add a new "Pricing Pack v2" with different business rules without breaking the existing system.

### The Challenge

How do we introduce new validation logic and parsing rules for `v2` pricing documents while ensuring that existing `v1` clients continue to function perfectly?

### The Solution: A "Plugin" Approach

#### 1. API Versioning
We introduce a new endpoint for the `v2` functionality. The original endpoint remains untouched, guaranteeing backward compatibility.

- **`POST /api/analyze/v1`** (or `/api/analyze`): Continues to use the original `PricingValidator`
- **`POST /api/analyze/v2`**: Routes requests to the new `PricingValidatorV2`

#### 2. Modular & Extensible Components
We create new classes that inherit from or compose the originals. We add, but never modify, existing code.

- A new `PricingParserV2` can be written to handle a new document format
- A new `PricingValidatorV2` can implement the new business rules
- The document classification logic in the main service will detect the `v2` format and route the data to these new components

#### 3. Dynamic Rule Loading
The RAG system can load different sets of rules based on the document version.

- When a `v1` document is analyzed, it loads rules R1-R5
- When a `v2` document is analyzed, it can load rules R1-R5 *plus* new rules R6 and R7 (e.g., "SaaS Pricing Transparency")

This "plugin" model ensures the system is **open for extension but closed for modification**, a core principle of robust software design. It allows us to continuously add features and adapt to new requirements without risking the stability of the existing application.

---

## 🎯 Key Architectural Benefits

### Scalability
- **Horizontal scaling**: Add more servers to handle increased load
- **Component-level scaling**: Scale individual services based on demand
- **Queue-based processing**: Handle traffic spikes gracefully

### Maintainability
- **Clear separation of concerns**: Each module has a single responsibility
- **Modular design**: Components can be updated independently
- **Comprehensive error handling**: Graceful degradation when components fail

### Extensibility
- **Plugin architecture**: New features can be added without breaking existing ones
- **Version support**: Multiple API versions can coexist
- **Configuration-driven**: Behavior can be modified without code changes

### Reliability
- **Stateless design**: No single point of failure
- **Persistent storage**: Data survives system restarts
- **Fallback mechanisms**: System continues to function even when AI services are unavailable

This architecture demonstrates how thoughtful design decisions made early in development can provide a solid foundation for both immediate functionality and long-term growth.
---