# AI Prompts & Safety Guidelines

This document outlines the AI prompting strategies, safety guardrails, and abstention policies implemented in the GSA Document Analyzer system.

---

## 🎯 Core Prompting Philosophy

The system employs a **hybrid approach** combining deterministic validation with AI-powered analysis to ensure reliability, accuracy, and safety in government document processing.

### Design Principles

1. **Structured Prompting**: All AI interactions use well-defined, structured prompts with clear expectations and output formats
2. **Evidence-Based Analysis**: AI is only asked to analyze pre-validated data and deterministically detected issues
3. **JSON-Constrained Outputs**: All AI responses are constrained to structured JSON format to prevent hallucination
4. **Rule-Grounded Context**: AI operations are always grounded in retrieved GSA rule context via RAG
5. **Conservative Abstention**: System abstains from AI analysis when safety conditions are not met

---

## 📝 Prompt Templates

### 1. Compliance Analysis Prompt

**Purpose**: Generate structured compliance checklist based on detected issues and retrieved rules.

**Template Structure**:
- **Role Definition**: "You are a GSA compliance expert"
- **Task Specification**: Analyze vendor data for specific GSA rules
- **Input Constraints**: Only analyze pre-detected issues with evidence
- **Output Format**: Strict JSON schema requirement
- **Abstention Instructions**: Do not fabricate issues or evidence

**Key Safety Elements**:
- Issues are pre-validated by deterministic checks
- Evidence is pre-extracted and provided
- Rule IDs are pre-matched via vector retrieval
- No creative interpretation allowed

### 2. Negotiation Brief Generation

**Purpose**: Create internal briefing document for procurement officers.

**Template Structure**:
- **Role Definition**: "GSA procurement specialist preparing negotiation brief"
- **Length Constraints**: Under 200 words, 2 paragraphs maximum
- **Content Requirements**: Strengths analysis and risk assessment
- **Tone Guidelines**: Professional, actionable, specific

**Safety Guardrails**:
- Based only on validated compliance data
- No speculation about vendor intentions
- Factual analysis of documented submissions only

### 3. Client Communication Generation

**Purpose**: Generate professional vendor communication about submission status.

**Template Structure**:
- **Role Definition**: "GSA contracting officer"
- **Tone Requirements**: Professional, encouraging, actionable
- **Content Structure**: Thanks, status, issues, next steps
- **Format Requirements**: Professional email with subject line

**Safety Features**:
- No legal advice or commitments
- Based only on technical compliance analysis
- Encouraging tone to maintain vendor relationships

---

## 🛡️ Safety Guardrails

### Input Validation Guardrails

1. **PII Sanitization**: All documents are automatically redacted before AI processing
2. **Schema Validation**: Input data must conform to predefined Pydantic schemas
3. **Size Limits**: Document content is truncated to prevent token limit issues
4. **Type Checking**: All inputs are validated for expected data types

### Output Validation Guardrails

1. **JSON Parsing**: All AI outputs must parse as valid JSON or system falls back
2. **Schema Compliance**: Responses are validated against expected output schemas
3. **Required Field Checking**: Missing required fields trigger fallback mechanisms
4. **Content Filtering**: Outputs are checked for inappropriate content

### Processing Guardrails

1. **API Rate Limiting**: Built-in retry logic with exponential backoff
2. **Token Management**: Automatic prompt truncation to stay within model limits
3. **Error Handling**: Comprehensive exception handling with fallback responses
4. **Logging**: All AI interactions are logged for audit and debugging

---

## 🚫 Abstention Policy

The system implements a **conservative abstention policy** to ensure reliability and safety in government procurement processes.

### When the System Abstains

1. **AI Service Unavailable**: When Gemini API or embeddings service is down
2. **Invalid Input Data**: When document parsing fails or data is malformed
3. **JSON Parsing Failure**: When AI generates non-parseable responses
4. **Missing Required Context**: When rule retrieval fails or returns empty results
5. **Token Limit Exceeded**: When input data exceeds model context limits
6. **Rate Limit Hit**: When API quotas are exhausted

### Abstention Mechanisms

#### 1. Graceful Fallback
When AI services fail, the system automatically falls back to:
- **Rule-Based Analysis**: Deterministic compliance checking only
- **Template Responses**: Pre-written professional communications
- **Manual Review Flags**: Clear indicators that human review is required

#### 2. Error Communication
- **User Notifications**: Clear explanation of system limitations
- **Fallback Quality**: Ensures fallback responses maintain professional standards
- **Manual Review Triggers**: Automatic escalation to human reviewers

#### 3. Audit Logging
- **Failure Tracking**: All abstention events are logged with reasons
- **Performance Monitoring**: System tracks abstention rates for improvement
- **Error Analysis**: Regular review of failure patterns for system enhancement

### Fallback Response Examples

**Compliance Analysis Fallback**:
