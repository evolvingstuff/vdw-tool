# Feature Plan: Track Redacted Sections in Front Matter

## 1. Audit Current Conversion Flow
- locate the code path that produces the JSON front matter and examine the existing TODO around redaction
- understand how censored versus included sections are currently identified during conversion

## 2. Design Metadata Update
- decide on the exact structure for the new `sections_included` and `sections_excluded` arrays
- confirm how section indices are derived (zero- or one-based) so the metadata is consistent

## 3. Implement Conversion Changes
- replace the placeholder array inserted today with the two new arrays while keeping existing redaction behavior
- ensure the front matter remains valid JSON and the rest of the document output is unaffected

## 4. Manual Verification
- run the converter on representative wiki content to inspect the new metadata and confirm it reflects the censored vs included sections
