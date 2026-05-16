# Workflow: Parse a Slip

1. Identify whether the user supplied an image or text.
2. For images, use vision to extract only fields needed for tracking.
3. Do not repeat private identifiers such as QR/barcodes, ticket numbers, account IDs, names, balances, or payment details.
4. Extract each leg:
   - match
   - competition if visible
   - kickoff date/time if visible
   - exact market wording
   - odds if visible
5. Mark unclear fields as unclear rather than guessing.
6. If team names are ambiguous, ask for league/date confirmation before tracking.
7. Show a parsed preview and ask the user to correct errors before tracking.

## Preview requirements

Include:

- numbered legs
- original market wording
- normalized market category when possible
- visible odds if supplied
- unclear or ambiguous fields
- unsupported-market warnings
- privacy/persistence note
- explicit confirmation question

Do not create a cron job from a parsed slip until the user clearly confirms.
