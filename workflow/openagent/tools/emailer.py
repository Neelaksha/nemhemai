# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart


# def send_email(to_email: str, subject: str, body: str):

#     # ⚠️ CHANGE THESE
#     sender_email = "your_email@gmail.com"
#     app_password = "your_app_password"  # NOT your normal password

#     try:
#         msg = MIMEMultipart()
#         msg["From"] = sender_email
#         msg["To"] = to_email
#         msg["Subject"] = subject

#         msg.attach(MIMEText(body, "plain"))

#         # Gmail SMTP
#         with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
#             server.login(sender_email, app_password)
#             server.send_message(msg)

#         return f"✅ Email sent to {to_email}"

#     except Exception as e:
#         return f"❌ Email failed: {str(e)}"





def send_email(to_email: str, subject: str, body: str):

    
    """
    Central email logic (for now fake, later real SMTP)
    """

    # 🔥 You can add logging, formatting, validation here
    if not to_email:
        return "❌ No email provided"

    # Simulate sending
    print("📧 Sending email...")
    print("TO:", to_email)
    print("SUBJECT:", subject)
    print("BODY:", body)

    # ✅ Return message (this is what shows in chat)
    return f"✅ Email sent to {to_email}"