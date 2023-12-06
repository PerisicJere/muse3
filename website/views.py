import os
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user, logout_user
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from . import db
from website.models import Review, ArtLocation
from sqlalchemy import text
import base64
from website.map_creator import create_folium_map
from better_profanity import profanity

views = Blueprint('views', __name__)


@views.route('/reviews')
@login_required
def reviews():
    images = ArtLocation.query.all()

    return render_template('all_reviews.html', user=current_user, ArtLocation=images)


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

    db.session.close()

    return review_count[0] if review_count else 0


@views.route('/')
def home():
    search_query = request.args.get('search')
    sort_option = request.args.get('sort')
    sort_by_option = request.args.get('sort_by')

    if sort_option == 'desc':
        sort_order = 'DESC'
    else:
        sort_order = 'ASC'

    if sort_by_option == 'reviews':
        order_by = 'ORDER BY review_count ' + sort_order
    elif sort_by_option == 'rating':
        order_by = 'ORDER BY COALESCE(avgRating, 0) ' + sort_order
    else:
        order_by = ''

    if search_query:
        sql_query = text(f"""
            SELECT al.location_id, al.location_name, al.location_image, al.description, 
                   COUNT(r.review_id) AS review_count, ROUND(AVG(r.stars), 1) as avgRating
            FROM artLocation al
            LEFT JOIN review r ON al.location_id = r.location_id
            WHERE al.location_name LIKE :search_query
            GROUP BY al.location_id
            {order_by}
        """)
        result = db.session.execute(sql_query, {"search_query": f"%{search_query}%"})
    else:
        sql_query = text(f"""
            SELECT al.location_id, al.location_name, al.location_image, al.description, 
                   COUNT(r.review_id) AS review_count, ROUND(AVG(r.stars), 1) as avgRating
            FROM artLocation al
            LEFT JOIN review r ON al.location_id = r.location_id
            GROUP BY al.location_id
            {order_by}
        """)
        result = db.session.execute(sql_query)

    images = [
        {
            "location_id": row.location_id,
            "location_name": row.location_name,
            "location_image": base64.b64encode(row.location_image).decode('utf-8'),
            "description": row.description,
            "num_reviews": row.review_count,
            "average_rating": row.avgRating
        }
        for row in result
    ]
    return render_template('home.html', user=current_user, ArtLocation=images)


@views.route('/map', methods=['GET', 'POST'])
def map():
    if request.method == 'POST':
        selected_type = request.form.get('location_type', 'all')
        search_query = request.form.get('search', '')
    else:
        selected_type = request.args.get('location_type', 'all')
        search_query = request.args.get('search', '')

    if selected_type != 'all' and search_query is None:
        m = create_folium_map(selected_type)
    else:
        m = create_folium_map(selected_type, search_query)

    folium_map_html = m.get_root().render()

    return render_template('map_resize.html', user=current_user, folium_map_html=folium_map_html)


@views.route('/all_reviews', methods=['GET', 'POST'])
def all_reviews():
    if request.method == 'POST':
        # This block handles the review submission
        stars = int(request.form.get('stars'))
        comment = request.form.get('comment')
        location_id = request.form.get('location_id')
        review_image = request.files.get('review_image')

        if location_id is not None:
            # Call the submit_review function
            submit_review(stars, comment, location_id, review_image, current_user.user_id)
        else:
            flash('Location ID is missing in the form submission.', category='error')
            # Handle the error or redirect to an error page as needed

    # This block handles the GET request for displaying reviews
    search_query = request.args.get('search')
    sort_option = request.args.get('sort')
    location_id = request.args.get('location_id')
    min_rating = request.args.get('min_rating', type=float, default=0)

    if sort_option == 'desc':
        sort_order = 'DESC'
    else:
        sort_order = 'ASC'

    sql_query = text(f"""
        SELECT r.stars, r.comment, r.review_image, u.displayName
        FROM review r
        LEFT JOIN user u ON r.user_id = u.user_id
        WHERE r.location_id = :location_id AND r.comment IS NOT NULL AND r.stars >= :min_rating
        ORDER BY r.stars {sort_order}
    """)
    location_name_query = text("""SELECT location_name FROM artLocation WHERE location_id = :location_id""")
    location_name = db.session.execute(location_name_query, {"location_id": location_id}).scalar()
    result = db.session.execute(sql_query, {"location_id": location_id, "min_rating": min_rating})

    reviews = [
        {
            "stars": row.stars,
            "comment": row.comment,
            "review_image": base64.b64encode(row.review_image).decode('utf-8') if row.review_image else None,
            "displayName": row.displayName,
        }
        for row in result
    ]
    star_base64 = star_icon('star.png')

    return render_template('all_reviews.html', user=current_user, reviews=reviews, location_id=location_id,
                           star_base64=star_base64, location_name=location_name)


def star_icon(img_name):
    image_path = 'website/icons/' + img_name
    with open(image_path, 'rb') as image_file:
        star_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    return star_base64


def profanity_filter(x):
    profanity.load_censor_words()
    profanity_is_true = profanity.contains_profanity(x)
    if profanity_is_true:
        return True


def submit_review(stars, comment, location_id, review_image, user_id):
    if review_image:
        filename = secure_filename(review_image.filename)
        review_image_path = os.path.join('uploads', filename)
        review_image.save(review_image_path)
    else:
        review_image_path = None

    try:
        # Call the profanity filter function
        if profanity_filter(comment):
            flash('Profanity detected in the comment.', category='error')
            return redirect('/error')

        # Insert the review into the database
        db.session.execute(
            """
            INSERT INTO review (stars, comment, review_image, user_id, location_id)
            VALUES (:stars, :comment, :review_image, :user_id, :location_id)
            """,
            {
                "stars": stars,
                "comment": comment,
                "review_image": review_image_path,
                "user_id": user_id,
                "location_id": location_id,
            }
        )

        # Check the integrity constraint for the stars rating
        if stars < 0 or stars > 5:
            raise ValueError("Value for stars must be between 0 and 5.")

        # Commit the transaction (Flask-SQLAlchemy will handle this automatically)
        db.session.commit()

        flash('Review submitted successfully!', category='success')

        redirect_url = f'/reviews?location_id={location_id}'
        return redirect(redirect_url)

    except IntegrityError as e:
        # Handle integrity constraint violations (e.g., unique constraint)
        flash('Integrity error: Duplicate entry or other constraint violation.', category='error')
        return redirect('/error')

    except ValueError as e:
        # Handle invalid stars rating
        flash(f'Stars need to be from 1 to 5, you entered {stars}', category='error')
        return redirect('/error')

    except Exception as e:
        flash(f'Stars need to be from 1 to 5, you entered {stars}', category='error')
        return redirect('/error')  # Redirect to an error page or handle the error appropriately


@views.route('/user_profile', methods=['GET'])
@login_required
def user_profile():
    # Using raw SQL to fetch reviews for the current user
    user_reviews_query = text("""
        SELECT r.stars, r.comment, al.location_name
        FROM MUSE_DB.review r
        JOIN MUSE_DB.artLocation al ON r.location_id = al.location_id
        WHERE r.user_id = :user_id
        ORDER BY r.stars DESC
    """)

    result = db.session.execute(user_reviews_query, {"user_id": current_user.user_id})

    user_reviews = [
        {
            "stars": row.stars,
            "comment": row.comment,
            "location_name": row.location_name,
        }
        for row in result
    ]
    star_base64 = star_icon('star.png')
    return render_template('user_profile.html', user=current_user, user_reviews=user_reviews, star_base64=star_base64)


def onDeleteUserTrigger(user_id):
    # First ASF
    # Creates a trigger that automatically deletes a user's reviews when the user account is deleted
    with db.engine.connect() as connection:
        query = text("""
            DROP TRIGGER IF EXISTS `delete_user_reviews`;
            CREATE TRIGGER delete_user_reviews
            BEFORE DELETE ON user
            FOR EACH ROW
            BEGIN
                DELETE FROM review WHERE user_id = :user_id;
            END;
        """)
        connection.execute(query, {"user_id": user_id})


@views.route('/delete_account', methods=['POST', 'GET'])
@login_required
def delete_account():
    if request.method == 'POST':
        user_id = current_user.get_id()
        onDeleteUserTrigger(user_id)

        db.session.commit()
        logout_user()

        return redirect(url_for('home'))

    return render_template('delete_account.html', user=current_user)


@views.route('/top_reviewers')
def top_reviewers():
    # Using raw SQL to fetch the top 10 reviewers
    sql_query = text("""
        SELECT user.user_id, user.displayName, COUNT(review.review_id) AS num_reviews
        FROM user
        INNER JOIN review ON review.user_id = user.user_id
        GROUP BY user.user_id
        ORDER BY num_reviews DESC
        LIMIT 10
    """)

    result = db.session.execute(sql_query)
    top_reviewers = [
        {
            "user_id": row.user_id,
            "displayName": row.displayName,
            "num_reviews": row.num_reviews,
        }
        for row in result
    ]

    return render_template('top_reviewers.html', user=current_user, top_reviewers=top_reviewers)
