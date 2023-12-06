import csv
from faker import Faker
import random

fake = Faker()


def get_random_image():
    num = random.randint(1,4)
    if num == 1:
        with open('image_links.txt', 'r') as file:
            image_links = file.readlines()
        return random.choice(image_links).strip()
    else:
        return None


def generate_fake_review():
    user_id = random.randint(1, 200)
    location_id = random.randint(1, 80)
    stars = random.randint(1, 5)
    comment = fake.text()
    review_image = get_random_image()

    return [user_id, location_id, stars, comment, review_image]


num_reviews = 2671

header = ['user_id', 'location_id', 'stars', 'comment', 'review_image']

with open('fake_reviews.csv', 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)

    csv_writer.writerow(header)

    for _ in range(num_reviews):
        fake_review = generate_fake_review()
        csv_writer.writerow(fake_review)

print(f"Fake reviews saved to 'fake_reviews.csv'")
