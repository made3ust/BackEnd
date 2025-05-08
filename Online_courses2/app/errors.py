from flask import render_template, flash, redirect, request, url_for
from app import app, db

@app.errorhandler(404)
def not_found_error(error):
   return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
   return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_error(error):
   try:
       db.session.rollback()
       app.logger.error(f"Internal server error encountered: {error}", exc_info=True)
   except Exception as e:
       app.logger.error(f"Error during rollback in 500 handler: {e}")
   return render_template('errors/500.html'), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    flash('Upload error: File is too large (max 16MB).', 'danger')
    return redirect(request.referrer or url_for('main.courses_view')), 413