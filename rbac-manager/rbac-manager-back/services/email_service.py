# backend/services/email_service.py
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import logging

logger = logging.getLogger(__name__)

# Configuración SMTP desde variables de entorno
SMTP_HOST = os.getenv('SMTP_HOST', 'email-smtp.us-east-1.amazonaws.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM = os.getenv('SMTP_FROM', SMTP_USER)

def test_smtp_connection() -> dict:
    """Prueba la conexión SMTP y retorna el estado"""
    if not SMTP_USER or not SMTP_PASSWORD:
        return {
            "success": False,
            "message": "SMTP credentials not configured. Set SMTP_USER and SMTP_PASSWORD"
        }
    
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            return {"success": True, "message": f"Connected to {SMTP_HOST}:{SMTP_PORT}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def send_email(to_emails: List[str], subject: str, body_html: str, body_text: str = None) -> bool:
    """
    Envía un correo electrónico a una lista de destinatarios.
    Retorna True si se envió correctamente, False en caso contrario.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured. Email not sent.")
        print("⚠️ SMTP no configurado. Email no enviado.")
        return False
    
    if not to_emails:
        logger.warning("No recipient emails provided.")
        return False
    
    # Filtrar emails vacíos
    to_emails = [e for e in to_emails if e and e.strip()]
    if not to_emails:
        return False
    
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_FROM
        msg['To'] = ', '.join(to_emails)
        
        # Versión texto plano (fallback)
        if body_text:
            part_text = MIMEText(body_text, 'plain')
            msg.attach(part_text)
        
        # Versión HTML
        part_html = MIMEText(body_html, 'html')
        msg.attach(part_html)
        
        # Conectar y enviar
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent to {', '.join(to_emails)}")
        print(f"📧 Email sent to {', '.join(to_emails)}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {e}")
        print(f"❌ SMTP Authentication failed. Check your SMTP_USER and SMTP_PASSWORD")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        print(f"❌ SMTP error: {e}")
        return False

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        print(f"❌ Failed to send email: {e}")
        return False


def send_certificate_alert_email(to_emails: List[str], username: str, days_until: int, expiry_date: str) -> bool:
    """
    Envía una alerta de certificado próximo a expirar.
    """

    # Obtener el nombre del cluster desde variable de entorno
    cluster_name = os.getenv('RBAC_CLUSTER_NAME', 'Unknown Cluster')

    subject = f"⚠️ ALERTA: Certificado de {username} expira en {days_until} días"
    
    # Determinar nivel de urgencia
    if days_until <= 5:
        urgency_color = "#dc3545"
        urgency_level = "CRÍTICO"
        urgency_emoji = "🔴"
    elif days_until <= 15:
        urgency_color = "#ffc107"
        urgency_level = "ADVERTENCIA"
        urgency_emoji = "🟡"
    else:
        urgency_color = "#fd7e14"
        urgency_level = "ATENCIÓN"
        urgency_emoji = "🟠"    

    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #282c34; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f8f9fa; }}
            .alert-box {{ 
                background-color: {urgency_color}; 
                color: {'#856404' if days_until <= 15 else 'white'};
                padding: 15px; 
                border-radius: 8px; 
                text-align: center;
                margin: 20px 0;
            }}
            .info {{ margin: 15px 0; padding: 10px; background-color: white; border-radius: 5px; }}
            .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #666; }}
            .badge {{
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🔐 RBAC Manager</h2>
                <h3>Alerta de Certificado</h3>
            </div>
            <div class="content">
                <div class="alert-box">
                    <h3 style="margin: 0;">{urgency_emoji} Nivel: {urgency_level}</h3>
                </div>
                
                <p>Estimado administrador,</p>
                
                <p>El certificado del usuario <strong>{username}</strong> está próximo a expirar en el cluster <strong>{cluster_name}</strong>.</p>
                
                <div class="info">
                    <strong>📋 Detalles:</strong><br>
                    • Usuario: {username}<br>
                    • Cluster: {cluster_name}<br>
                    • Días restantes: <strong style="color: {urgency_color};">{days_until} días</strong><br>
                    • Fecha de expiración: {expiry_date}<br>
                </div>
                
                <div class="info">
                    <strong>📌 Acciones recomendadas:</strong><br>
                    • Ingresar al sistema y generar un nuevo kubeconfig para el usuario<br>
                    • El usuario podrá renovar su certificado desde la interfaz<br>
                    • La regeneración del certificado no afecta los permisos del usuario
                </div>
                <hr style="margin: 20px 0;">
                <p style="font-size: 12px; color: #666; text-align: center;">
                    Este es un mensaje automático del sistema RBAC Manager.<br>
                    Por favor no responder a este correo.
                </p>
            </div>
            <div class="footer">
                <p>© 2024 RBAC Manager - Sistema de Gestión de Accesos</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    body_text = f"""
    {urgency_emoji} ALERTA: Certificado de {username} expira en {days_until} días
    
    Nivel: {urgency_level}
    
    Detalles:
    - Usuario: {username}
    - Cluster: {cluster_name}
    - Días restantes: {days_until} días
    - Fecha de expiración: {expiry_date}
    
    Acciones recomendadas:
    - Ingresar al sistema y generar un nuevo kubeconfig para el usuario
    - El usuario podrá renovar su certificado desde la interfaz
    - La regeneración del certificado no afecta los permisos del usuario
    
    ---
    RBAC Manager - Sistema de Gestión de Accesos
    """
    
    return send_email(to_emails, subject, body_html, body_text)

def send_certificate_report_email(to_emails: List[str], expiring_certificates: List[dict], days_threshold: int) -> bool:
    """
    Envía un reporte consolidado con todos los certificados próximos a expirar.
    """
    cluster_name = os.getenv('RBAC_CLUSTER_NAME', 'Unknown Cluster')
    total_certs = len(expiring_certificates)
    critical_count = len([c for c in expiring_certificates if c['days_until_expiry'] <= 5])
    warning_count = len([c for c in expiring_certificates if 5 < c['days_until_expiry'] <= 15])
    attention_count = len([c for c in expiring_certificates if 15 < c['days_until_expiry'] <= 30])
    
    subject = f"📊 RBAC Manager Report - {total_certs} certificate(s) expiring in next {days_threshold} days"
    
    # Generar filas de la tabla HTML
    table_rows = ""
    for cert in expiring_certificates:
        # Color de fondo según urgencia
        row_color = "#f8d7da" if cert['days_until_expiry'] <= 5 else "#fff3cd" if cert['days_until_expiry'] <= 15 else "#ffe8d6"
        status_color = "#dc3545" if cert['days_until_expiry'] <= 5 else "#ffc107" if cert['days_until_expiry'] <= 15 else "#fd7e14"
        
        table_rows += f"""
        <tr style="background-color: {row_color};">
            <td style="padding: 10px; border: 1px solid #ddd;"><strong>{cert['username']}</strong></td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">
                <span style="display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; background-color: {status_color}; color: white;">
                    {cert['status_text']}
                </span>
            </td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: {status_color};">{cert['days_until_expiry']} días</td>
            <td style="padding: 10px; border: 1px solid #ddd;">{cert['expiry_date_str']}</td>
            <td style="padding: 10px; border: 1px solid #ddd;">{cert['cert_days']} días</td>
        </tr>
        """
    
    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #282c34; color: white; padding: 20px; text-align: center; }}
            .summary {{ display: flex; gap: 15px; justify-content: center; margin: 20px 0; }}
            .summary-box {{ padding: 10px 20px; border-radius: 8px; text-align: center; }}
            .summary-box.critical {{ background-color: #dc3545; color: white; }}
            .summary-box.warning {{ background-color: #ffc107; color: #856404; }}
            .summary-box.attention {{ background-color: #fd7e14; color: white; }}
            .summary-box.total {{ background-color: #6c757d; color: white; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th {{ background-color: #e8eaf6; padding: 12px; text-align: left; border: 1px solid #ddd; }}
            .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🔐 RBAC Manager</h2>
                <h3>Reporte de Certificados por Expirar</h3>
            </div>
            
            <div class="summary">
                <div class="summary-box critical">
                    <strong>🔴 Críticos</strong><br>
                    {critical_count}
                </div>
                <div class="summary-box warning">
                    <strong>🟡 Advertencia</strong><br>
                    {warning_count}
                </div>
                <div class="summary-box attention">
                    <strong>🟠 Atención</strong><br>
                    {attention_count}
                </div>
                <div class="summary-box total">
                    <strong>📊 Total</strong><br>
                    {total_certs}
                </div>
            </div>
            
            <p>Se han detectado <strong>{total_certs} certificado(s)</strong> que expirarán en los próximos <strong>{days_threshold} días</strong> en el cluster <strong>{cluster_name}</strong>.</p>
            
            <h3>📋 Certificados próximos a expirar:</h3>
            
            <table>
                <thead>
                    <tr>
                        <th>Usuario</th>
                        <th>Estado</th>
                        <th>Días Restantes</th>
                        <th>Fecha Expiración</th>
                        <th>Días Certificado</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            
            <div class="footer">
                <p>Este es un mensaje automático del sistema RBAC Manager.<br>
                Por favor no responder a este correo.</p>
                <p>© 2025 RBAC Manager - Sistema de Gestión de Accesos</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    body_text = f"""
    📊 REPORTE RBAC MANAGER - CERTIFICADOS POR EXPIRAR
    
    Cluster: {cluster_name}
    Total certificados próximos a expirar ({days_threshold} días): {total_certs}
    
    Resumen:
    - Críticos (≤5 días): {critical_count}
    - Advertencia (6-15 días): {warning_count}
    - Atención (16-30 días): {attention_count}
    
    Detalle de certificados:
    """
    
    for cert in expiring_certificates:
        body_text += f"""
    - {cert['username']}: {cert['status_text']} - {cert['days_until_expiry']} días (expira: {cert['expiry_date_str']})
    """
    
    body_text += """
    ---
    RBAC Manager - Sistema de Gestión de Accesos
    """
    
    return send_email(to_emails, subject, body_html, body_text)