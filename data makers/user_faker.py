import csv
from faker import Faker
from werkzeug.security import generate_password_hash

fake = Faker()


def generate_fake_user():
    plaintext_password = fake.password()
    hashed_password = generate_password_hash(plaintext_password, method="pbkdf2:sha256")
    display_name = fake.user_name()
    email = fake.email()

    return [plaintext_password, display_name, email], [hashed_password, display_name, email]


num_users = 200

plaintext_header = ['password', 'displayName', 'email']
hashed_header = ['hashed_password', 'displayName', 'email']

with open('fake_users_plaintext_passwords.csv', 'w', newline='') as plaintext_file, \
        open('fake_users_hashed_passwords.csv', 'w', newline='') as hashed_file:
    plaintext_csv_writer = csv.writer(plaintext_file)
    hashed_csv_writer = csv.writer(hashed_file)

    plaintext_csv_writer.writerow(plaintext_header)
    hashed_csv_writer.writerow(hashed_header)

    for _ in range(num_users):
        plaintext_user, hashed_user = generate_fake_user()
        plaintext_csv_writer.writerow(plaintext_user)
        hashed_csv_writer.writerow(hashed_user)

print(f"Fake users with plaintext passwords saved to 'fake_users_plaintext_passwords.csv'")
print(f"Fake users with hashed passwords saved to 'fake_users_hashed_passwords.csv'")
