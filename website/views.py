import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, make_response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import db
from website.models import Review, ArtLocation
from sqlalchemy import text
import base64
from website.map_creator import create_folium_map

views = Blueprint('views', __name__)


@views.route('/reviews')
@login_required
def reviews():

    images = ArtLocation.query.all()

    return render_template('reviews.html', user=current_user, ArtLocation=images)




@views.route('/add_review', methods=['POST'])
@login_required
def add_review():
    stars = int(request.form.get('star-rating'))
    comment = request.form.get('comment')

    image_file = request.files['image']
    if image_file:
        filename = secure_filename(image_file.filename)
        review_image = os.path.join('uploads', filename)
        image_file.save(review_image)
    else:
        review_image = None

    new_review = Review(
        stars=stars,
        comment=comment,
        review_image=review_image,
        user_id=current_user.user_id
    )

    db.session.add(new_review)
    db.session.commit()

    flash('Review added successfully!', category='success')
    return redirect(url_for('views.home'))


def get_num_reviews(location_id):
    sql_query = text("""
        SELECT COUNT(review_id) AS reviewCount
        FROM review
        WHERE location_id = :location_id;
    """)

    result = db.session.execute(sql_query, {"location_id": location_id})
    review_count = result.fetchone()

    # Close the cursor and connection
    db.session.close()

    return review_count[0] if review_count else 0


from sqlalchemy import desc, asc

@views.route('/')
def home():
    search_query = request.args.get('search')
    sort_option = request.args.get('sort')  # New line to get the sort option from the URL

    if search_query:
        # If there is a search query, filter images based on the name
        sql_query = text("""
            SELECT al.location_id, al.location_name, al.location_image, al.description, COUNT(r.review_id) AS review_count
            FROM artLocation al
            LEFT JOIN review r ON al.location_id = r.location_id
            WHERE al.location_name LIKE :search_query
            GROUP BY al.location_id
        """)
        result = db.session.execute(sql_query, {"search_query": f"%{search_query}%"})
    else:
        # If no search query, retrieve all images with review count
        sql_query = text("""
            SELECT al.location_id, al.location_name, al.location_image, al.description, COUNT(r.review_id) AS review_count
            FROM artLocation al
            LEFT JOIN review r ON al.location_id = r.location_id
            GROUP BY al.location_id
        """)
        result = db.session.execute(sql_query)

    # Sort the images based on user preference
    if sort_option == 'reviews_desc':
        result = sorted(result, key=lambda x: x.review_count, reverse=True)
    elif sort_option == 'reviews_asc':
        result = sorted(result, key=lambda x: x.review_count)
    # Add more sorting options if needed in the future

    images = [
        {
            "location_id": row.location_id,
            "location_name": row.location_name,
            "location_image": base64.b64encode(row.location_image).decode('utf-8'),
            "description": row.description,
            "num_reviews": row.review_count
        }
        for row in result
    ]

    return render_template('home.html', user=current_user, ArtLocation=images)





@views.route('/reviews/<int:location_id>', endpoint='location_reviews')
def reviews(location_id):
    sql_query = text("SELECT stars, comment, review_image FROM review WHERE location_id = %s ")
    reviews = db.session.execute(sql_query, location_id)
    return render_template('reviews.html', reviews_data=reviews,user=current_user)


@views.route('/map', methods=['GET', 'POST'])
def map():
    should_have_border = True

    if request.method == 'POST':
        selected_type = request.form.get('location_type', 'all')
    else:
        selected_type = request.args.get('location_type', 'all')

    m = create_folium_map(selected_type)

    folium_map_html = m.get_root().render()

    return render_template('map_resize.html', should_have_border=should_have_border, user=current_user, folium_map_html=folium_map_html)

