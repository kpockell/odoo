import os
import logging
from odoo import http
from odoo.http import request
from odoo.modules.module import get_module_path

_logger = logging.getLogger(__name__)


class WellKnownController(http.Controller):
    
    # Test route to verify controller is working
    @http.route('/wellknown_test', type='http', auth='none')
    def test(self):
        return "Controller is working!"
    
    @http.route('/.well-known/pki-validation/<string:filename>', type='http', auth='none', csrf=False, save_session=False)
    def wellknown_pki_validation(self, filename, **kw):
        """
        Serve files from .well-known/pki-validation directory.
        This is commonly used for SSL certificate validation.
        """
        _logger.info(f"=== WellKnown route called for filename: {filename} ===")
        try:
            # Get the module path and construct the file path
            module_path = get_module_path('custom_wellknown')
            if not module_path:
                _logger.error("Module 'custom_wellknown' not found")
                return request.not_found()
            
            filepath = os.path.join(module_path, 'static', '.well-known', 'pki-validation', filename)
            
            if not os.path.exists(filepath) or not os.path.isfile(filepath):
                _logger.warning(f"File not found: {filepath}")
                return request.not_found()
            
            # Read and serve the file
            with open(filepath, 'rb') as f:
                content = f.read()
            
            return request.make_response(
                content,
                headers=[
                    ('Content-Type', 'text/plain'),
                    ('Cache-Control', 'public, max-age=3600'),
                ]
            )
        except Exception as e:
            _logger.error(f"Error serving /.well-known/pki-validation/{filename}: {e}")
            return request.not_found()
