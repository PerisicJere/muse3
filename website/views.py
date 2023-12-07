import json
import os
import re
import mysql.connector
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user, logout_user
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from . import db
from website.models import Review, ArtLocation, User
from sqlalchemy import text
import base64
from website.map_creator import create_folium_map
from better_profanity import profanity


views = Blueprint('views', __name__)



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
        stars = int(request.form.get('stars'))
        comment = request.form.get('comment')
        location_id = request.form.get('location_id')
        review_image = request.files.get('review_image')

        if location_id is not None:
            submit_review(stars, comment, location_id, process_review_image(review_image), current_user.user_id)
        else:
            flash('Location ID is missing in the form submission.', category='error')

    search_query = request.args.get('search')
    sort_option = request.args.get('sort')
    location_id = request.args.get('location_id')
    min_rating = request.args.get('min_rating', type=int, default=0)

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


def process_review_image(review_image):
    if review_image:
        try:
            image_data = review_image.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            return base64_image
        except Exception as e:
            flash(f'Error processing review image: {e}', category='error')
            return None
    return None


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


def submit_review(stars, comment, location_id, base64_image, user_id):
    if base64_image:
        try:
            if profanity_filter(comment):
                flash('Profanity detected in the comment.', category='error')
                return redirect('/error')

            db.session.execute(
                text("""
                    INSERT INTO review (stars, comment, review_image, user_id, location_id)
                    VALUES (:stars, :comment, :review_image, :user_id, :location_id)
                    """),
                {
                    "stars": stars,
                    "comment": comment,
                    "review_image": base64_image,  # Pass base64-encoded data directly to the database
                    "user_id": user_id,
                    "location_id": location_id,
                }
            )

            if stars < 1 or stars > 5:
                raise ValueError("Value for stars must be between 1 and 5.")

            db.session.commit()
            flash('Review submitted successfully!', category='success')
            redirect_url = '/'
            print(redirect_url)
            return redirect(redirect_url)

        except IntegrityError as e:
            flash('Integrity error: Duplicate entry or other constraint violation.', category='error')
            db.session.rollback()
            return redirect('/error')

        except ValueError as e:
            # Handle invalid stars rating
            flash(f'Stars need to be from 1 to 5, you entered {stars}', category='error')
            db.session.rollback()
            return redirect('/error')

        except Exception as e:
            flash(f'{e}', category='error')
            db.session.rollback()
            return redirect('/error')

    else:
        try:
            if profanity_filter(comment):
                flash('Profanity detected in the comment.', category='error')
                return redirect('/error')

            db.session.execute(
                text("""
                    INSERT INTO review (stars, comment, user_id, location_id)
                    VALUES (:stars, :comment, :user_id, :location_id)
                    """),
                {
                    "stars": stars,
                    "comment": comment,
                    "user_id": user_id,
                    "location_id": location_id,
                }
            )

            if stars < 1 or stars > 5:
                raise ValueError("Value for stars must be between 1 and 5.")

            db.session.commit()
            flash('Review submitted successfully!', category='success')
            redirect_url = '/'
            print(redirect_url)
            return redirect(redirect_url)

        except IntegrityError as e:
            flash('Integrity error: Duplicate entry or other constraint violation.', category='error')
            db.session.rollback()
            return redirect('/error')

        except ValueError as e:
            # Handle invalid stars rating
            flash(f'Stars need to be from 1 to 5, you entered {stars}', category='error')
            db.session.rollback()
            return redirect('/error')

        except Exception as e:
            flash(f'{e}', category='error')
            db.session.rollback()
            return redirect('/error')

@views.route('/user_profile', methods=['GET'])
@login_required
def user_profile():
    # Using raw SQL to fetch reviews for the current user
    user_reviews_query = text("""
        SELECT r.stars, r.comment, al.location_name, r.review_image
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
            "review_image": base64.b64encode(row.review_image).decode('utf-8') if row.review_image else "",
        }
        for row in result
    ]
    star_base64 = star_icon('star.png')
    return render_template('user_profile.html', user=current_user, user_reviews=user_reviews, star_base64=star_base64)
def create_delete_user_trigger():
    # Get the directory of the current Python script
    current_dir = os.path.dirname(os.path.realpath(__file__))

    # Construct the absolute path to connectorConfig.json
    config_file_path = os.path.join(current_dir, "connectorConfig.json")

    try:
        with open(config_file_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: '{config_file_path}' file not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding '{config_file_path}': {e}")
        return

    connection_config = config.get("mysql")
    if not connection_config:
        print("Error: MySQL configuration not found in 'connectorConfig.json'.")
        return

    try:
        connection = mysql.connector.connect(**connection_config)
        cursor = connection.cursor()

        # Drop the trigger if it already exists
        cursor.execute("DROP TRIGGER IF EXISTS delete_user_trigger")

        # Create the trigger
        create_trigger_query = """
        CREATE TRIGGER delete_user_trigger
        BEFORE DELETE ON user
        FOR EACH ROW
        BEGIN
            DELETE FROM review WHERE user_id = OLD.user_id;
        END;
        """
        cursor.execute(create_trigger_query)

        # Commit the changes
        connection.commit()

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if 'cursor' in locals() and cursor is not None:
            cursor.close()

        if 'connection' in locals() and connection.is_connected():
            connection.close()

create_delete_user_trigger()

@views.route('/delete_account', methods=['POST', 'GET'])
@login_required
def delete_user():
    if request.method == 'POST':
        user_id_to_delete = current_user.user_id
        print(user_id_to_delete)

        try:
            # Assuming the 'User' and 'Review' tables exist
            db.session.delete(current_user)
            db.session.commit()

            print(f"User with ID {user_id_to_delete} and associated reviews deleted successfully.")

            logout_user()
            return redirect(url_for('auth.sign_up'))
        except Exception as e:
            print(f"Error deleting user: {e}")

    # If the request method is GET, render the delete account confirmation page
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
