# Automated Reasoning for Policy Validation: Specification 

## 1) Executive Summary

This specification defines a system that **validates AI outputs against formalized policies** using automated reasoning. 
Inputs (a user query, a model’s answer, and a policy) are translated into logic, checked with a solver, and returned as one of several **validation result types** with explanations and confidence scores. 
This document contains **only specification and examples**—no code.

---

## 2) Core Concepts (Glossary)

* **Policy**: A set of typed variables and logical rules that encode business requirements.
* **Premises**: Facts extracted from the user’s query (context/conditions).
* **Claims**: Assertions extracted from the model’s answer.
* **Translation**: Mapping natural language to logic with a per-statement confidence.
* **Validation**: Logical checking that determines whether claims follow from premises and policy.

---

## 3) System Overview

### 3.1 Inputs

* **Query**: Natural language question or scenario.
* **Content**: The model’s answer to the query.
* **Policy**: Formal definition (variables, types, and rules).
* **Confidence Threshold**: Minimum translation confidence required for a statement to enter proof.

### 3.2 Processing Stages

1. **Translation**: Extract premises and claims; map them to policy variables and relations. Each mapping has a confidence in [0.0, 1.0].
2. **Logic Construction**: Build a constraint set from premises, policy rules, and the (negated) claims.
3. **Solving**:

   * If `premises ∧ policy_rules ∧ ¬claims` is **UNSAT** ⇒ claims are **VALID**.
   * If it is **SAT** but `premises ∧ policy_rules ∧ claims` is **SAT** ⇒ **SATISFIABLE** (consistent but not enforced).
   * If `premises ∧ policy_rules ∧ claims` is **UNSAT** while the first is **SAT** ⇒ **INVALID**.
   * If the solver returns **UNKNOWN** or translation lacks sufficient confidence ⇒ **IMPOSSIBLE**.
4. **Result**: Return result type, findings, variable assignments (when helpful), rules applied, and suggestions.

### 3.3 Result Types

* **VALID**: The claims logically follow from the premises and policy.
* **INVALID**: The claims contradict the premises and/or policy.
* **SATISFIABLE**: The claims are consistent but not guaranteed by the policy.
* **IMPOSSIBLE**: The system cannot determine validity (e.g., low confidence, solver unknown).
* **TRANSLATION_AMBIGUOUS**: Detected ambiguity that would make proof unsound.
* **NO_TRANSLATIONS**: Nothing in the input could be mapped to the policy.
* **TOO_COMPLEX**: Input exceeds complexity/latency bounds.

---

## 4) Formal Specification

### 4.1 Data Models (Conceptual)

**Variable**

```
{
  "name": "String",              // unique identifier
  "type": "Boolean|Integer|Real|String|CustomType",
  "description": "String"
}
```

**Rule**

```
{
  "id": "String",
  "natural_language": "String",
  "formal_logic": "LogicExpression",     // abstract form
  "variables_referenced": ["String", ...]
}
```

**Policy**

```
{
  "name": "String",
  "description": "String",
  "variables": [Variable, ...],
  "rules": [Rule, ...],
  "custom_types": [/* optional */]
}
```

**ValidationRequest**

```
{
  "query": "String",
  "content": "String",
  "policy": Policy,
  "confidence_threshold": 0.0..1.0
}
```

**LogicStatement**

```
{
  "natural_language": "String",
  "formal_logic": "String",       // abstract notation
  "confidence": 0.0..1.0
}
```

**Finding**

```
{
  "premises": [LogicStatement, ...],
  "claims": [LogicStatement, ...],
  "variable_assignments": { "name": "value", ... },   // when available
  "rules_applied": ["RuleID", ...],
  "suggestions": ["String", ...]                      // for INVALID or weak cases
}
```

**ValidationResult**

```
{
  "result": "VALID|INVALID|SATISFIABLE|IMPOSSIBLE|TRANSLATION_AMBIGUOUS|NO_TRANSLATIONS|TOO_COMPLEX",
  "findings": [Finding, ...],
  "confidence": 0.0..1.0
}
```

### 4.2 Translation Specification

**Function shape (conceptual)**
`translate(text, policy) → (logic_expression(s), confidence)`

* Produces **premises** (from query) and **claims** (from content).
* Assigns **confidence** per statement. Only statements with confidence ≥ `confidence_threshold` are used in proof.
* If critical mappings fall below threshold, return **TRANSLATION_AMBIGUOUS** (or **IMPOSSIBLE** if mapping is structurally impossible).

### 4.3 Decision Rules (Deterministic)

Given:

* `Φ` = policy rules
* `P` = premises
* `C` = claims

Evaluate:

1. If translation yields no usable statements ⇒ **NO_TRANSLATIONS**.
2. If translation includes unresolved ambiguities above risk threshold ⇒ **TRANSLATION_AMBIGUOUS**.
3. Else attempt solving:

   * If `P ∧ Φ ∧ ¬C` is UNSAT ⇒ **VALID**.
   * Else if `P ∧ Φ ∧ C` is UNSAT and `P ∧ Φ ∧ ¬C` is SAT ⇒ **INVALID**.
   * Else if `P ∧ Φ ∧ C` is SAT ⇒ **SATISFIABLE**.
   * Else ⇒ **IMPOSSIBLE**.
4. If input size or formula exceeds limits ⇒ **TOO_COMPLEX**.

---

## 5) Sample Policy (used for all examples)

```
{
  "name": "HR-Policy",
  "description": "Eligibility for parental leave",
  "variables": [
    { "name": "is_full_time", "type": "Boolean", "description": "Employee is full-time" },
    { "name": "years_of_service", "type": "Integer", "description": "Whole years employed" },
    { "name": "eligible_for_parental_leave", "type": "Boolean", "description": "Eligibility flag" }
  ],
  "rules": [
    {
      "id": "R1",
      "natural_language": "Full-time employees with ≥ 1 year of service are eligible for parental leave.",
      "formal_logic": "(is_full_time ∧ years_of_service ≥ 1) ⇒ eligible_for_parental_leave",
      "variables_referenced": ["is_full_time","years_of_service","eligible_for_parental_leave"]
    },
    {
      "id": "R2",
      "natural_language": "Employees who are not full-time are not eligible for parental leave.",
      "formal_logic": "¬is_full_time ⇒ ¬eligible_for_parental_leave",
      "variables_referenced": ["is_full_time","eligible_for_parental_leave"]
    }
  ]
}
```

---

## 6) Worked Examples (Inputs & Expected Outputs)

> All examples use the **Sample Policy** above and specify a `confidence_threshold`.
> The `formal_logic` strings in findings are illustrative (not executable code).

### Example A — **VALID**

**Input (ValidationRequest)**

```
{
  "query": "Am I eligible for parental leave if I've worked here for 2 years full-time?",
  "content": "Yes, you are eligible for parental leave because you meet the requirements.",
  "policy": <HR-Policy>,
  "confidence_threshold": 0.60
}
```

**Expected Output (ValidationResult)**

```
{
  "result": "VALID",
  "confidence": 0.90,
  "findings": [
    {
      "premises": [
        {
          "natural_language": "Employee is full-time.",
          "formal_logic": "is_full_time = true",
          "confidence": 0.95
        },
        {
          "natural_language": "Employee has 2 years of service.",
          "formal_logic": "years_of_service = 2",
          "confidence": 0.95
        }
      ],
      "claims": [
        {
          "natural_language": "Employee is eligible for parental leave.",
          "formal_logic": "eligible_for_parental_leave = true",
          "confidence": 0.90
        }
      ],
      "variable_assignments": {
        "is_full_time": "true",
        "years_of_service": "2",
        "eligible_for_parental_leave": "true"
      },
      "rules_applied": ["R1"],
      "suggestions": []
    }
  ]
}
```

---

### Example B — **INVALID**

**Input**

```
{
  "query": "I am a part-time employee with 3 years at the company. Am I eligible?",
  "content": "Yes, you are eligible.",
  "policy": <HR-Policy>,
  "confidence_threshold": 0.60
}
```

**Expected Output**

```
{
  "result": "INVALID",
  "confidence": 0.88,
  "findings": [
    {
      "premises": [
        { "natural_language": "Employee is not full-time.", "formal_logic": "is_full_time = false", "confidence": 0.95 },
        { "natural_language": "Employee has 3 years of service.", "formal_logic": "years_of_service = 3", "confidence": 0.90 }
      ],
      "claims": [
        { "natural_language": "Employee is eligible for parental leave.", "formal_logic": "eligible_for_parental_leave = true", "confidence": 0.90 }
      ],
      "variable_assignments": {},
      "rules_applied": ["R2"],
      "suggestions": [
        "Clarify eligibility exceptions for part-time employees if any exist.",
        "Revise the answer to reflect policy R2: part-time employees are not eligible."
      ]
    }
  ]
}
```

---

### Example C — **SATISFIABLE** (policy permits but does not enforce)

**Input**

```
{
  "query": "I am full-time but just started last month. Am I eligible yet?",
  "content": "Yes, you are eligible.",
  "policy": <HR-Policy>,
  "confidence_threshold": 0.60
}
```

**Rationale**: Premises imply `is_full_time = true` and `years_of_service = 0` (or <1).

* R1 does **not** force eligibility (since years < 1).
* R2 does **not** forbid eligibility (since full-time).
  Thus claim can be **consistent** but not **entailed**.

**Expected Output**

```
{
  "result": "SATISFIABLE",
  "confidence": 0.80,
  "findings": [
    {
      "premises": [
        { "natural_language": "Employee is full-time.", "formal_logic": "is_full_time = true", "confidence": 0.95 },
        { "natural_language": "Employee has less than 1 year of service.", "formal_logic": "years_of_service = 0", "confidence": 0.80 }
      ],
      "claims": [
        { "natural_language": "Employee is eligible.", "formal_logic": "eligible_for_parental_leave = true", "confidence": 0.85 }
      ],
      "variable_assignments": {},
      "rules_applied": [],
      "suggestions": [
        "State explicitly that eligibility requires ≥ 1 year for a definitive YES.",
        "If policy allows provisional eligibility, encode an exception rule."
      ]
    }
  ]
}
```

---

### Example D — **TRANSLATION_AMBIGUOUS**

**Input**

```
{
  "query": "I work here on a fixed schedule and do overtime often; does that make me eligible?",
  "content": "Yes, you are eligible.",
  "policy": <HR-Policy>,
  "confidence_threshold": 0.75
}
```

**Rationale**: The system cannot safely map “fixed schedule” to `is_full_time` with ≥0.75 confidence; mapping would be guesswork.

**Expected Output**

```
{
  "result": "TRANSLATION_AMBIGUOUS",
  "confidence": 0.50,
  "findings": [
    {
      "premises": [],
      "claims": [
        { "natural_language": "Employee is eligible.", "formal_logic": "eligible_for_parental_leave = true", "confidence": 0.70 }
      ],
      "variable_assignments": {},
      "rules_applied": [],
      "suggestions": [
        "Clarify employment status (full-time vs part-time).",
        "Provide years of service in whole years."
      ]
    }
  ]
}
```

---

### Example E — **NO_TRANSLATIONS**

**Input**

```
{
  "query": "What’s the cafeteria menu tomorrow?",
  "content": "The special is pasta.",
  "policy": <HR-Policy>,
  "confidence_threshold": 0.60
}
```

**Expected Output**

```
{
  "result": "NO_TRANSLATIONS",
  "confidence": 1.00,
  "findings": [
    {
      "premises": [],
      "claims": [],
      "variable_assignments": {},
      "rules_applied": [],
      "suggestions": [
        "Provide a question relevant to HR eligibility or use a policy that covers cafeteria services."
      ]
    }
  ]
}
```

---

### Example F — **IMPOSSIBLE** (solver unknown or insufficient evidence)

**Input**

```
{
  "query": "I'm on a fractional 0.75 FTE contract since 10 months; can I get parental leave?",
  "content": "No, you cannot.",
  "policy": <HR-Policy>,
  "confidence_threshold": 0.60
}
```

**Rationale**: The policy uses Integer years; mapping “10 months” and fractional FTE requires types/rules not present. The system cannot reliably decide under current policy/typing.

**Expected Output**

```
{
  "result": "IMPOSSIBLE",
  "confidence": 0.70,
  "findings": [
    {
      "premises": [
        { "natural_language": "Employment fraction is 0.75 FTE.", "formal_logic": "unsupported_type:FTE", "confidence": 0.80 },
        { "natural_language": "Tenure is 10 months.", "formal_logic": "unsupported_unit:months", "confidence": 0.85 }
      ],
      "claims": [
        { "natural_language": "Not eligible for parental leave.", "formal_logic": "eligible_for_parental_leave = false", "confidence": 0.80 }
      ],
      "variable_assignments": {},
      "rules_applied": [],
      "suggestions": [
        "Extend policy with Real/Duration types and conversion rules (months→years).",
        "Define eligibility for fractional FTE explicitly."
      ]
    }
  ]
}
```

---

### Example G — **TOO_COMPLEX**

**Input**

```
{
  "query": "We have 500 employees with varying contracts across 12 subsidiaries. Are all employees in groups A–L eligible given exceptions in sections 4.1–4.12 and the 87 special cases in Appendix B?",
  "content": "Yes, all are eligible.",
  "policy": <HR-Policy>,
  "confidence_threshold": 0.60
}
```

**Expected Output**

```
{
  "result": "TOO_COMPLEX",
  "confidence": 1.00,
  "findings": [
    {
      "premises": [],
      "claims": [
        { "natural_language": "All employees are eligible.", "formal_logic": "∀e. eligible(e)", "confidence": 0.70 }
      ],
      "variable_assignments": {},
      "rules_applied": [],
      "suggestions": [
        "Partition the query by subsidiary or exception class.",
        "Summarize special cases into parametric rules and re-run in batches."
      ]
    }
  ]
}
```

---

## 7) Quality, Safety & Audit Requirements

* **Confidence Gating**: Only statements with confidence ≥ threshold participate in proof. Others are ignored but logged.
* **Explainability**: Always return recognized premises, checked claims, applied rules, and—when applicable—example assignments/counterexamples.
* **Change Control**: Policies are versioned; each result references the policy version and a digest of inputs.
* **Time & Units**: Policies should declare unit conventions (e.g., years vs months). Cross-unit inputs must be normalized or rejected with guidance.
* **Performance Limits**: Establish clear size/time caps; exceedance returns **TOO_COMPLEX** with partitioning advice.

---

## 8) Minimal Conformance Checklist

A system claiming conformance to this spec MUST:

1. Accept `ValidationRequest` and return `ValidationResult` with one of the enumerated result types.
2. Implement confidence-threshold gating for translation.
3. Follow the decision rules in §4.3 exactly.
4. Include findings with premises, claims, rules applied, and suggestions (where relevant).
5. Emit **NO_TRANSLATIONS**, **TRANSLATION_AMBIGUOUS**, **IMPOSSIBLE**, or **TOO_COMPLEX** as defined, when applicable.
6. Preserve policy versions and input hashes for auditability.

## Reference

[AWS implementation](https://aws.amazon.com/blogs/machine-learning/minimize-generative-ai-hallucinations-with-amazon-bedrock-automated-reasoning-checks/)
