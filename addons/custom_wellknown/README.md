# Well-Known Static Files Module

This module provides support for serving files from the `/.well-known/pki-validation/` path, commonly used for SSL certificate validation.

## Usage

1. **Install the module:**
   - Restart Odoo server
   - Go to Apps menu
   - Click "Update Apps List"
   - Search for "Well-Known Static Files"
   - Click Install

2. **Add your validation files:**
   - Place your certificate validation files in:
     ```
     addons/custom_wellknown/static/.well-known/pki-validation/
     ```
   - Example: `addons/custom_wellknown/static/.well-known/pki-validation/your-validation-file.txt`

3. **Access your files:**
   - Files will be accessible at: `http://yourdomain/.well-known/pki-validation/your-validation-file.txt`

## Example

If you place a file at:
```
addons/custom_wellknown/static/.well-known/pki-validation/certificate-validation.txt
```

It will be accessible at:
```
http://localhost/.well-known/pki-validation/certificate-validation.txt
```

## Notes

- Files are served with `text/plain` content type
- No authentication required (`auth='none'`)
- CSRF protection disabled for public access
- Files are cached for 1 hour
