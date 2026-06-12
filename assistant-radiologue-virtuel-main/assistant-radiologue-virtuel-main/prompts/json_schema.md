# JSON output schema

```json
{
  "image_quality": "good | limited | poor",
  "predicted_class": "normal | suspected_opacity | uncertain",
  "confidence": 0.0,
  "visual_evidence": ["string"],
  "justification": "string",
  "limitations": ["string"],
  "warning": "Prototype pédagogique. Non destiné au diagnostic. Validation par un professionnel qualifié requise."
}
```

## Validation rules

- `predicted_class` must be one of: `normal`, `suspected_opacity`, `uncertain`.
- `confidence` must be numeric between 0 and 1.
- `warning` must be present.
- `visual_evidence` must not contain patient history.
- If image quality is poor, prefer `uncertain`.
