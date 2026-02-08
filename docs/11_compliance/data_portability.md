# Data Portability

Your data is yours.

**Last Updated:** February 8, 2026
**Audience:** Product Managers

> **Before Reading This**
>
> You should understand:
> - [GDPR Compliance](./gdpr_compliance.md)
> - [API Reference](../07_api_reference/rest_api.md)

## The Export Feature

Under GDPR Article 20, users have the right to receive their data in a "structured, commonly used and machine-readable format."

We provide a "Download My Data" button.
It generates a ZIP file containing:
- Profile data (JSON)
- Task history (JSON)
- Uploaded files (Original format)

## API Access

Users can also simply query the API to scrape their own data.
Our API is fully inclusive of the data model.

## Transfer to Competitors

We do not implement "Vendor Lock-in." The JSON schema is documented so it can be mapped to other systems.

## Related Reading

- [Right to Erasure](./right_to_erasure.md)
- [GDPR Compliance](./gdpr_compliance.md)
