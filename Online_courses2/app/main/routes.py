from flask import render_template, request, current_app
from flask_login import current_user
from sqlalchemy import or_
from app import db
from app.models import Course
from app.forms import SearchForm
from flask import Blueprint

main_bp = Blueprint('main', __name__, template_folder='../templates')

@main_bp.app_context_processor
def base():
    """Makes the search form available in all templates."""
    form = SearchForm()
    return dict(search_form=form)

@main_bp.route('/')
def courses_view():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('query', '').strip()

    query_filter = Course.query

    if search_query:
        query_filter = query_filter.filter(
            or_(
                Course.title.ilike(f'%{search_query}%'),
                Course.instructor.ilike(f'%{search_query}%')
            )
        )
        title = f'Search Results: "{search_query}"'
    else:
        title = 'Available Courses'

    courses = query_filter.order_by(Course.date_posted.desc()).paginate(
        page=page, per_page=current_app.config.get('COURSES_PER_PAGE', 6)
    )

    return render_template('index.html', courses=courses, title=title, query=search_query)