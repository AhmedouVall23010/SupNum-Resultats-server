import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from app.core.config import settings


class EmailService:
    @staticmethod
    def _get_verification_email_template(verification_link: str, email: str) -> str:
        """Generate beautiful HTML email template for email verification"""
        return f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vérification de votre email - SupNum Résultats</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
            <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f4f4f4; padding: 20px;">
                <tr>
                    <td align="center" style="padding: 20px 0;">
                        <table role="presentation" style="width: 600px; max-width: 100%; background-color: #ffffff; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: 1px;">
                                        SupNum Résultats
                                    </h1>
                                    <p style="color: #ffffff; margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                                        Plateforme de Résultats
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <h2 style="color: #333333; margin: 0 0 20px 0; font-size: 24px; font-weight: 600;">
                                        Bienvenue sur SupNum Résultats !
                                    </h2>
                                    
                                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                        Bonjour,
                                    </p>
                                    
                                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                        Merci de vous être inscrit sur <strong>SupNum Résultats</strong>, la plateforme de résultats de l'Institut Supérieur du Numérique.
                                    </p>
                                    
                                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                        Pour finaliser votre inscription et accéder à votre compte, veuillez confirmer votre adresse email en cliquant sur le bouton ci-dessous :
                                    </p>
                                    
                                    <!-- Button -->
                                    <table role="presentation" style="width: 100%; margin: 30px 0;">
                                        <tr>
                                            <td align="center" style="padding: 15px 0;">
                                                <a href="{verification_link}" 
                                                   style="display: inline-block; padding: 15px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">
                                                    Vérifier mon email
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="color: #999999; font-size: 14px; line-height: 1.6; margin: 30px 0 0 0;">
                                        Si le bouton ne fonctionne pas, copiez et collez le lien suivant dans votre navigateur :
                                    </p>
                                    
                                    <p style="color: #667eea; font-size: 14px; line-height: 1.6; margin: 10px 0 0 0; word-break: break-all;">
                                        <a href="{verification_link}" style="color: #667eea; text-decoration: none;">{verification_link}</a>
                                    </p>
                                    
                                    <div style="border-top: 1px solid #e0e0e0; margin: 40px 0 20px 0; padding-top: 20px;">
                                        <p style="color: #999999; font-size: 12px; line-height: 1.6; margin: 0;">
                                            <strong>Note importante :</strong> Ce lien est valide pendant 24 heures. Si vous n'avez pas créé de compte sur <strong>SupNum Résultats</strong>, veuillez ignorer cet email.
                                        </p>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e0e0e0;">
                                    <p style="color: #666666; font-size: 14px; margin: 0 0 10px 0;">
                                        <strong>SupNum</strong> - Plateforme de Résultats
                                    </p>
                                    <p style="color: #999999; font-size: 12px; margin: 0 0 10px 0;">
                                        Institut Supérieur du Numérique
                                    </p>
                                    <p style="color: #999999; font-size: 12px; margin: 0;">
                                        © {datetime.now().year} Institut Supérieur du Numérique. Tous droits réservés.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    @staticmethod
    def send_verification_email(email: str, verification_token: str) -> bool:
        """Send email verification link to user"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_FROM
            msg['To'] = email
            msg['Subject'] = "Vérification de votre email - SupNum"
            
            # Create verification link
            verification_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
            
            # Get HTML template
            html_body = EmailService._get_verification_email_template(verification_link, email)
            
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Send email
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
                server.quit()
                return True
            else:
                # In development, just print the link
                print(f"Verification link for {email}: {verification_link}")
                return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    @staticmethod
    def _get_reset_password_email_template(reset_link: str, email: str) -> str:
        """Generate beautiful HTML email template for password reset"""
        return f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Réinitialisation de votre mot de passe - SupNum Résultats</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
            <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f4f4f4; padding: 20px;">
                <tr>
                    <td align="center" style="padding: 20px 0;">
                        <table role="presentation" style="width: 600px; max-width: 100%; background-color: #ffffff; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: 1px;">
                                        SupNum Résultats
                                    </h1>
                                    <p style="color: #ffffff; margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                                        Plateforme de Résultats
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <h2 style="color: #333333; margin: 0 0 20px 0; font-size: 24px; font-weight: 600;">
                                        Réinitialisation de votre mot de passe
                                    </h2>
                                    
                                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                        Bonjour,
                                    </p>
                                    
                                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                        Vous avez demandé à réinitialiser votre mot de passe pour votre compte <strong>SupNum Résultats</strong>.
                                    </p>
                                    
                                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                        Cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe :
                                    </p>
                                    
                                    <!-- Button -->
                                    <table role="presentation" style="width: 100%; margin: 30px 0;">
                                        <tr>
                                            <td align="center" style="padding: 15px 0;">
                                                <a href="{reset_link}" 
                                                   style="display: inline-block; padding: 15px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">
                                                    Réinitialiser mon mot de passe
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="color: #999999; font-size: 14px; line-height: 1.6; margin: 30px 0 0 0;">
                                        Si le bouton ne fonctionne pas, copiez et collez le lien suivant dans votre navigateur :
                                    </p>
                                    
                                    <p style="color: #667eea; font-size: 14px; line-height: 1.6; margin: 10px 0 0 0; word-break: break-all;">
                                        <a href="{reset_link}" style="color: #667eea; text-decoration: none;">{reset_link}</a>
                                    </p>
                                    
                                    <div style="border-top: 1px solid #e0e0e0; margin: 40px 0 20px 0; padding-top: 20px;">
                                        <p style="color: #999999; font-size: 12px; line-height: 1.6; margin: 0;">
                                            <strong>Note importante :</strong> Ce lien est valide pendant 1 heure. Si vous n'avez pas demandé de réinitialisation de mot de passe, veuillez ignorer cet email. Votre mot de passe ne sera pas modifié.
                                        </p>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e0e0e0;">
                                    <p style="color: #666666; font-size: 14px; margin: 0 0 10px 0;">
                                        <strong>SupNum</strong> - Plateforme de Résultats
                                    </p>
                                    <p style="color: #999999; font-size: 12px; margin: 0 0 10px 0;">
                                        Institut Supérieur du Numérique
                                    </p>
                                    <p style="color: #999999; font-size: 12px; margin: 0;">
                                        © {datetime.now().year} Institut Supérieur du Numérique. Tous droits réservés.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    @staticmethod
    def send_reset_password_email(email: str, reset_token: str) -> bool:
        """Send password reset link to user"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_FROM
            msg['To'] = email
            msg['Subject'] = "Réinitialisation de votre mot de passe - SupNum Résultats"
            
            # Create reset link
            reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
            
            # Get HTML template
            html_body = EmailService._get_reset_password_email_template(reset_link, email)
            
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Send email
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
                server.quit()
                return True
            else:
                # In development, just print the link
                print(f"Reset password link for {email}: {reset_link}")
                return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

