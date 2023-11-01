


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Email configuration
sender_email = 'sahniak9868@gmail.com'
sender_password = 'lqtndyskhwdochlw'
recipient_email = 'sahniak56@gmail.com'
subject = 'CSV File Attached'

# Create a MIME multipart message
message = MIMEMultipart()
message['From'] = sender_email
message['To'] = recipient_email
message['Subject'] = subject

# Email body
body = "Hello, please find the attached CSV file."
message.attach(MIMEText(body, 'plain'))

# Attach the CSV file
csv_file_path = 'line_diff.csv'
with open(csv_file_path, 'rb') as file:
    part = MIMEApplication(file.read())
    part.add_header('Content-Disposition', 'attachment', filename='m.csv')
    message.attach(part)

# Connect to the SMTP server
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = message.as_string()
    server.sendmail(sender_email, recipient_email, text)
    print("Email sent successfully!")
except Exception as e:
    print("Error sending email:", str(e))
finally:
    server.quit()
