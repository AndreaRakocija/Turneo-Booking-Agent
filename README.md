# Turneo Booking Query Service

This project implements a lightweight FastAPI application that interprets natural-language
queries about bookings (e.g. _“Show me bookings in November 2024 in USD”_) and returns
the total value of bookings on a particular date in the user-requested currency.


The service integrates:
- Turneo API (booking retrieval)
- FX conversion service
- Rule-based and OpenAI GPT function-calling parsers
- Clean architecture design for easy testing and maintainability

The deployed service is available here:

👉 **https://turneo-booking-agent.onrender.com/**  
(Interactive docs: `/docs`)

---

## 🧠 Overview

The core goal was to allow users to express a booking query naturally and receive:

- extracted date range
- target currency
- total value of bookings in that period (converted if needed)

To support reliable extraction, two parsers are used:

### **1. Rule-Based Parser**
Handles clear, unambiguous queries such as:
- “November 2024”
- “March 2023 in EUR”

### **2. OpenAI GPT Parser (Tools API)**
Used for more complex or conversational phrasing.  
Strict prompting ensures:
- function calling is always used
- no hallucinated dates

---

## 💡 Design Decisions & Trade-offs

### **Parser Fallback Strategy (OpenAI → Rule-Based)**
The system supports two parsing strategies:

1. **OpenAI GPT function-calling parser** — the primary parser when an OpenAI API key is available.
2. **Rule-based parser** — a deterministic fallback for simple month/year queries.

If no OpenAI API key is provided, the application automatically uses the rule-based parser.  
Even when an API key is available, if the OpenAI parser fails to extract a valid date range 
or returns an unsupported result, the system gracefully falls back to the rule-based parser 
before returning an error.


### **Default Currency = EUR**
When the user doesn't specify a currency, the system defaults to EUR, 
which aligns with common reporting practices in European booking environments.
A more robust production setup could also require explicit currency selection, 
but for the purposes of this challenge EUR serves as a practical and user-friendly default.


### **Experience Date vs. Booking Date**
Both the booking creation timestamp and the experience start time are 
valid ways to filter bookings, depending on the reporting context. 
For this service, I chose to use the experience start time (localTime/time) 
because it more accurately reflects when the activity is delivered and when 
revenue is typically recognized.

### **FX Conversion Provider**
Currency conversion is handled via a simple REST FX API (`fxratesapi.com`). The FX client retrieves a single
conversion rate for the required currency pair and simple in-memory caching is
implemented to avoid duplicate lookups within the same query.

### **LLM Evaluation**
LLM output is non-deterministic.  
A dedicated script (`scripts/eval_openai_parser.py`) evaluates parser behavior 
against test cases.

### **Graceful Handling of Unsupported Queries**
If no date is found in the query, the parser intentionally returns:
start_date="UNSUPPORTED", 
end_date="UNSUPPORTED".
The agent converts this into a clear message to the user.

---

## 🛠 Running Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 🔧 Configuration

Required environment variables:
```bash
export TURNEO_API_KEY="your-turneo-key"
export TURNEO_API_ROOT="https://api.san.turneo.co"

export OPENAI_API_KEY="your-openai-key" # optional

export FX_API_KEY="your-fx-key"   # optional
export FX_API_ROOT="https://api.fxratesapi.com"
```

A .env file is supported automatically.

## ▶️ Usage Example
### **Request:**

POST /query
```json
{
  "query": "Show me bookings in December 2025 in USD"
}
```
### **Response:**

```json
{
    "message": "The total value of bookings between 2025-12-01 and 2025-12-31 was 3,525.45 USD.",
    "total_value": 3525.45,
    "currency": "USD"
}
```

## 🧪 Testing

Run all tests:
```bash
pytest
```

Includes:
- Rule-based parser tests 
- BookingService tests (with fake repository + fake FX)
- Smoke test for /query endpoint

## 🤖 GPT Parser Evaluation Script

This script evaluates how reliably the OpenAI parser extracts date ranges and currency fields:
```bash
python scripts/eval_openai_parser.py
```

Example output:
```yaml
 === OpenAI Parser Evaluation ===
Total queries:    4
Correct outputs:  4
Accuracy:         100.0%
```