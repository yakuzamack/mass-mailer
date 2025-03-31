import os
import smtplib
import ssl
import base64
import uuid
import random
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from email.header import Header
from typing import Dict, Any, Optional
from src.proxy import ProxyManager
from src.config import SMTP_CONFIGS, AUTH_CONFIG, EMAIL_CONFIG, validate_config
import time
import dns.resolver
import socket

class EmailSender:
    def __init__(self, config=None):
        self.config = config or {}
        self.smtp_config = self.config.get('smtp', []) if isinstance(self.config.get('smtp'), list) else [self.config.get('smtp', {})]
        self.email_config = self.config.get('email', EMAIL_CONFIG)
        self.proxy_manager = ProxyManager(self.config)
        self.max_retries = self.email_config.get('max_retries', 3)
        self.retry_delay = self.email_config.get('retry_delay', 5)
        self.current_smtp_index = 0
        self.auth_config = self.config.get('auth', AUTH_CONFIG)
        self.should_stop_rotation = False
        
    def _generate_random_string(self, length: int = 8) -> str:
        """Generate a random string for obfuscation."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        
    def _obfuscate_headers(self, msg: MIMEMultipart) -> None:
        """Obfuscate email headers to make tracking harder."""
        # Generate random values for obfuscation
        random_id = self._generate_random_string(32)
        random_timestamp = str(int(time.time() * 1000))
        random_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        random_port = random.randint(10000, 65535)
        random_hex = ''.join(random.choices(string.hexdigits, k=8))
        
        # Add obfuscated headers
        msg['X-Google-Smtp-Source'] = f"AGHT+{self._generate_random_string(32)}"
        msg['X-Received'] = f"by 2002:a05:{random_hex}:{random_hex}:{random_hex}:{random_hex} with SMTP id {self._generate_random_string(16)}"
        msg['ARC-Seal'] = f"i=1; a=rsa-sha256; t={random_timestamp}; cv=none; d=google.com; s=arc-20240605; b={self._generate_random_string(128)}"
        msg['ARC-Message-Signature'] = f"i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com; s=arc-20240605; h=subject:from:to:mime-version:message-id:date:precedence:list-unsubscribe:reply-to:dkim-signature; bh={self._generate_random_string(32)}; b={self._generate_random_string(128)}"
        msg['X-Authority-Analysis'] = f"v=2.4 cv={self._generate_random_string(8)} c=1 sm=1 tr=0 ts={self._generate_random_string(8)}"
        
        # Add anti-abuse headers
        msg['X-AntiAbuse'] = "This header was added to track abuse, please include it with any abuse report"
        msg['X-AntiAbuse: Primary Hostname'] = "gator3268.hostgator.com"
        msg['X-AntiAbuse: Original Domain'] = "gmail.com"
        msg['X-AntiAbuse: Originator/Caller UID/GID'] = "[47 12] / [47 12]"
        msg['X-AntiAbuse: Sender Address Domain'] = "diamantextanques.com.br"
        msg['X-BWhitelist'] = "no"
        
        # Add source headers
        msg['X-Source-IP'] = random_ip
        msg['X-Sender-IP'] = random_ip
        msg['X-Source-L'] = "No"
        msg['X-Exim-ID'] = f"1ty{self._generate_random_string(4)}-00000001{self._generate_random_string(4)}-{self._generate_random_string(4)}"
        msg['X-Source'] = ""
        msg['X-Source-Args'] = ""
        msg['X-Source-Dir'] = ""
        msg['X-Source-Sender'] = f"(smtp.diamantextanques.com.br) [{random_ip}]:{random_port}"
        msg['X-Source-Auth'] = "engenharia@diamantextanques.com.br"
        msg['X-Email-Count'] = str(random.randint(1, 100))
        msg['X-Org'] = "HG=hgshared;ORG=hostgator"
        msg['X-Source-Cap'] = "aHRkaWd0YWw7aHRkaWd0YWw7Z2F0b3IzMjY4Lmhvc3RnYXRvci5jb20="
        msg['X-Local-Domain'] = "yes"
        
        # Add random names for Received header
        random_names = [
            "Mohamed Giuliano", "Cfre Ferguson", "Meagan Linkewich", 
            "John Smith", "Sarah Johnson", "Michael Brown"
        ]
        msg['Received'] = random.choice(random_names)
        
    def _obfuscate_content(self, content: str) -> str:
        """Obfuscate email content to make tracking harder."""
        # Add random whitespace and line breaks
        lines = content.split('\n')
        obfuscated_lines = []
        for line in lines:
            if line.strip():
                # Add random spaces at the end of lines
                line = line.rstrip() + ' ' * random.randint(1, 3)
                # Randomly split long lines
                if len(line) > 70:
                    split_point = random.randint(50, 70)
                    line = line[:split_point] + '=\n' + ' ' * random.randint(1, 3) + line[split_point:]
            obfuscated_lines.append(line)
        return '\n'.join(obfuscated_lines)
        
    def send_email(self, to_email: str, to_name: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send an email to a recipient."""
        try:
            # Get current proxy configuration
            proxy_config = self.proxy_manager.get_current_proxy()
            
            # Create email message with proper headers
            msg = self._create_email_message(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content,
                proxy_config=proxy_config
            )
            
            # Verify email authentication
            if not self._verify_email_auth(self.email_config['from_email']):
                print(f"[WARNING] Email authentication verification failed for {self.email_config['from_email']}")
            
            # Send email through SMTP with retries
            for attempt in range(self.max_retries):
                try:
                    if self._send_smtp_email(msg, proxy_config):
                        return True
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise e
                    print(f"[WARNING] Attempt {attempt + 1} failed, retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    
            return False
            
        except Exception as e:
            print(f"Error sending email to {to_email}: {str(e)}")
            return False
        
    def _create_email_message(self,
                            to_email: str,
                            subject: str,
                            html_content: str,
                            plain_text_content: str,
                            from_email: str = None,
                            reply_to: str = None,
                            proxy_config: Dict[str, str] = None) -> MIMEMultipart:
        """Create an email message with proper headers."""
        # Generate a unique boundary with proper format
        boundary = f"==============={random.randint(1000000000000000000, 9999999999999999999)}=="
        
        msg = MIMEMultipart('mixed')
        
        # Set headers in exact order from example
        msg['Delivered-To'] = to_email
        msg['Received'] = f"by 2002:a05:{self._generate_random_string(8)}:{self._generate_random_string(8)}:b0:6b:{self._generate_random_string(8)}:{self._generate_random_string(8)} with SMTP id {self._generate_random_string(16)}lab;"
        msg['X-Google-Smtp-Source'] = f"AGHT+{self._generate_random_string(64)}"
        msg['X-Received'] = f"by 2002:a05:{self._generate_random_string(8)}:{self._generate_random_string(8)}:b0:7c5:{self._generate_random_string(8)}:{self._generate_random_string(8)} with SMTP id {self._generate_random_string(32)}-{self._generate_random_string(32)}c8a1mr{self._generate_random_string(32)}.15.{int(time.time() * 1000)};"
        msg['ARC-Seal'] = f"i=1; a=rsa-sha256; t={int(time.time())}; cv=none; d=google.com; s=arc-20240605; b={self._generate_random_string(256)}"
        msg['ARC-Message-Signature'] = f"i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com; s=arc-20240605; h=subject:from:to:mime-version:message-id:date:precedence:list-unsubscribe:reply-to:dkim-signature; bh={self._generate_random_string(32)}; b={self._generate_random_string(256)}; dara=google.com"
        msg['ARC-Authentication-Results'] = f"i=1; mx.google.com; dkim=pass header.i=@diamantextanques.com.br header.s=default header.b=\"{self._generate_random_string(16)}\"; spf=softfail (google.com: domain of transitioning {from_email or self.email_config['from_email']} does not designate {proxy_config['http'].split('://')[1].split(':')[0] if proxy_config else '127.0.0.1'} as permitted sender) smtp.mailfrom={from_email or self.email_config['from_email']}"
        msg['Return-Path'] = f"<{from_email or self.email_config['from_email']}>"
        msg['Received-SPF'] = f"softfail (google.com: domain of transitioning {from_email or self.email_config['from_email']} does not designate {proxy_config['http'].split('://')[1].split(':')[0] if proxy_config else '127.0.0.1'} as permitted sender) client-ip={proxy_config['http'].split('://')[1].split(':')[0] if proxy_config else '127.0.0.1'};"
        msg['Authentication-Results'] = f"mx.google.com; dkim=pass header.i=@diamantextanques.com.br header.s=default header.b=\"{self._generate_random_string(16)}\"; spf=softfail (google.com: domain of transitioning {from_email or self.email_config['from_email']} does not designate {proxy_config['http'].split('://')[1].split(':')[0] if proxy_config else '127.0.0.1'} as permitted sender) smtp.mailfrom={from_email or self.email_config['from_email']}"
        msg['Received'] = f"from omta040.useast.a.cloudfilter.net (omta040.useast.a.cloudfilter.net. [{proxy_config['http'].split('://')[1].split(':')[0] if proxy_config else '127.0.0.1'}]) by mx.google.com with ESMTPS id {self._generate_random_string(32)}-{self._generate_random_string(32)}d4esi{self._generate_random_string(32)}.652.2025.03.29.01.52.50 for <{to_email}> (version=TLS1_2 cipher=ECDHE-ECDSA-AES128-GCM-SHA256 bits=128/128);"
        msg['Received'] = f"from eig-obgw-5010a.ext.cloudfilter.net ([10.0.29.199]) by cmsmtp with ESMTPS id {self._generate_random_string(32)};"
        msg['Received'] = f"from gator3268.hostgator.com ([198.57.247.232]) by cmsmtp with ESMTPS id {self._generate_random_string(32)};"
        msg['X-Authority-Analysis'] = f"v=2.4 cv={self._generate_random_string(8)} c=1 sm=1 tr=0 ts={self._generate_random_string(8)} a={self._generate_random_string(32)}==:117 a={self._generate_random_string(32)}==:17 a={self._generate_random_string(16)}:10 a={self._generate_random_string(16)}:10 a={self._generate_random_string(16)}:10 a={self._generate_random_string(16)}:8 a={self._generate_random_string(16)}:9 a={self._generate_random_string(16)}:21 a={self._generate_random_string(16)}:10 a={self._generate_random_string(16)}:10 a={self._generate_random_string(16)}:10 a={self._generate_random_string(32)}:22 a={self._generate_random_string(32)}:22 a={self._generate_random_string(32)}:22"
        msg['DKIM-Signature'] = f"v=1; a=rsa-sha256; q=dns/txt; c=relaxed/relaxed; d=diamantextanques.com.br; s=default; h=Subject:From:To:MIME-Version:Content-Type:Message-ID:Date:List-Unsubscribe:Reply-To:Sender:Cc:Content-Transfer-Encoding:Content-ID:Content-Description:Resent-Date:Resent-From:Resent-Sender:Resent-To:Resent-Cc:Resent-Message-ID:In-Reply-To:References:List-Id:List-Help:List-Subscribe:List-Post:List-Owner:List-Archive; bh={self._generate_random_string(32)}; b={self._generate_random_string(256)};"
        msg['Received'] = f"from [{proxy_config['http'].split('://')[1].split(':')[0] if proxy_config else '127.0.0.1'}] (port={random.randint(10000, 65535)} helo=smtp.diamantextanques.com.br) by gator3268.hostgator.com with esmtpsa (TLS1.2) tls TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384 (Exim 4.98.1) (envelope-from <{from_email or self.email_config['from_email']}>) id {self._generate_random_string(16)}-{self._generate_random_string(16)}-{self._generate_random_string(4)} for {to_email};"
        msg['Reply-To'] = reply_to or from_email or self.email_config['from_email']
        msg['X-Source-IP'] = proxy_config['http'].split('://')[1].split(':')[0] if proxy_config else '127.0.0.1'
        msg['X-Sender-IP'] = proxy_config['http'].split('://')[1].split(':')[0] if proxy_config else '127.0.0.1'
        msg['X-Mailer'] = 'Microsoft Office Outlook, Build 10.0.5610'
        msg['X-MimeOLE'] = 'Produced By Microsoft MimeOLE V6.00.2800.1441'
        msg['List-Unsubscribe'] = f'<mailto:unsubscribe@diamantextanques.com.br>'
        msg['Precedence'] = 'first-class'
        msg['X-Anti-Abuse'] = f'Please report abuse to abuse@diamantextanques.com.br'
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = f'<{self._generate_random_string(32)}@diamantextanques.com.br>'
        msg['Received'] = random.choice([
            "Leon Weaver", "Lou Wei", "Arjan De", 
            "Mika Kaiser", "Marsha Kay", "Mohamed Giuliano"
        ])
        msg['Content-Type'] = f'multipart/mixed; boundary="{boundary}"'
        msg['MIME-Version'] = '1.0'
        msg['To'] = to_email
        msg['From'] = from_email or self.email_config['from_email']
        msg['Subject'] = Header(subject, 'utf-8')
        
        # Add anti-abuse headers
        msg['X-AntiAbuse'] = "This header was added to track abuse, please include it with any abuse report"
        msg['X-AntiAbuse: Primary Hostname'] = "gator3268.hostgator.com"
        msg['X-AntiAbuse: Original Domain'] = "gmail.com"
        msg['X-AntiAbuse: Originator/Caller UID/GID'] = "[47 12] / [47 12]"
        msg['X-AntiAbuse: Sender Address Domain'] = "diamantextanques.com.br"
        msg['X-BWhitelist'] = "no"
        msg['X-Source-L'] = "No"
        msg['X-Exim-ID'] = f"1ty{self._generate_random_string(4)}-00000001{self._generate_random_string(4)}-{self._generate_random_string(4)}"
        msg['X-Source'] = ""
        msg['X-Source-Args'] = ""
        msg['X-Source-Dir'] = ""
        msg['X-Source-Sender'] = f"(smtp.diamantextanques.com.br) [{proxy_config['http'].split('://')[1].split(':')[0] if proxy_config else '127.0.0.1'}]:{random.randint(10000, 65535)}"
        msg['X-Source-Auth'] = from_email or self.email_config['from_email']
        msg['X-Email-Count'] = str(random.randint(1, 100))
        msg['X-Org'] = "HG=hgshared;ORG=hostgator;"
        msg['X-Source-Cap'] = "aHRkaWd0YWw7aHRkaWd0YWw7Z2F0b3IzMjY4Lmhvc3RnYXRvci5jb20="
        msg['X-Local-Domain'] = "yes"
        msg['X-CMAE-Envelope'] = f"MS4xf{self._generate_random_string(200)}"
        
        # Create HTML part with proper boundary
        html_part = MIMEText(self._obfuscate_html_content(html_content), 'html', 'utf-8')
        html_part['Content-Type'] = 'text/html; charset="utf-8"'
        html_part['MIME-Version'] = '1.0'
        html_part['Content-Transfer-Encoding'] = 'quoted-printable'
        
        # Create plain text part with proper boundary
        plain_part = MIMEText(self._obfuscate_content(plain_text_content), 'plain', 'utf-8')
        plain_part['Content-Type'] = 'text/plain; charset="utf-8"'
        plain_part['MIME-Version'] = '1.0'
        plain_part['Content-Transfer-Encoding'] = 'quoted-printable'
        
        # Add parts to message
        msg.attach(html_part)
        msg.attach(plain_part)
        
        return msg
        
    def _obfuscate_html_content(self, content: str) -> str:
        """Obfuscate HTML content to match the example format."""
        # Split content into lines
        lines = content.split('\n')
        obfuscated_lines = []
        
        for line in lines:
            if line.strip():
                # Add random spaces at the end of lines
                line = line.rstrip() + ' ' * random.randint(1, 3)
                
                # Split long lines at random points
                if len(line) > 70:
                    # Find a good split point (not in the middle of a word)
                    words = line.split()
                    current_line = []
                    current_length = 0
                    
                    for word in words:
                        if current_length + len(word) + 1 > 70:
                            # Join current line and add soft break
                            obfuscated_lines.append(' '.join(current_line) + '=\n')
                            current_line = [word]
                            current_length = len(word)
                        else:
                            current_line.append(word)
                            current_length += len(word) + 1
                    
                    # Add the last line
                    if current_line:
                        obfuscated_lines.append(' '.join(current_line))
                else:
                    obfuscated_lines.append(line)
            else:
                obfuscated_lines.append(line)
        
        # Join lines and add trailing space
        return '\n'.join(obfuscated_lines) + '=20'
        
    def _verify_email_auth(self, email: str) -> bool:
        """Verify SPF and DKIM records for the sender domain."""
        try:
            # Skip verification in test environment
            if email.endswith('@example.com'):
                return True
                
            domain = email.split('@')[1]
            
            # Check SPF record
            try:
                spf_records = dns.resolver.resolve(domain, 'TXT')
                has_spf = any('v=spf1' in str(record) for record in spf_records)
            except dns.resolver.NXDOMAIN:
                has_spf = False
            
            # Check DKIM record
            try:
                dkim_records = dns.resolver.resolve(f'{self.auth_config["dkim_selector"]}._domainkey.{domain}', 'TXT')
                has_dkim = bool(dkim_records)
            except dns.resolver.NXDOMAIN:
                has_dkim = False
            
            if not has_spf:
                print(f"[WARNING] No SPF record found for {domain}")
            if not has_dkim:
                print(f"[WARNING] No DKIM record found for {domain}")
                
            return has_spf and has_dkim
            
        except Exception as e:
            print(f"[ERROR] Email authentication verification failed: {str(e)}")
            return False
            
    def _send_smtp_email(self, msg: MIMEMultipart, proxy_config: Dict[str, str]) -> bool:
        """Send email through SMTP server using proxy."""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Get current SMTP configuration
            current_smtp = self.smtp_config[self.current_smtp_index]
            print(f"[DEBUG] Using SMTP server: {current_smtp['host']}:{current_smtp['port']}")
            
            # Connect to SMTP server through proxy
            with smtplib.SMTP(
                current_smtp['host'],
                current_smtp['port'],
                timeout=current_smtp.get('timeout', 30)
            ) as server:
                server.set_debuglevel(1)  # Enable debug output
                print(f"[DEBUG] Connected to SMTP server")
                
                server.ehlo()
                print(f"[DEBUG] EHLO completed")
                
                # Start TLS if configured
                if current_smtp.get('use_tls', True):
                    server.starttls(context=context)
                    print(f"[DEBUG] TLS started")
                    server.ehlo()
                    print(f"[DEBUG] EHLO after TLS completed")
                    
                # Login with credentials
                try:
                    server.login(current_smtp['username'], current_smtp['password'])
                    print(f"[DEBUG] Login successful")
                except smtplib.SMTPAuthenticationError as e:
                    print(f"[ERROR] Authentication failed: {str(e)}")
                    return False
                
                # Send email
                try:
                    server.send_message(msg)
                    print(f"[DEBUG] Message sent successfully")
                except smtplib.SMTPException as e:
                    print(f"[ERROR] Failed to send message: {str(e)}")
                    return False
                
                # Rotate to next SMTP server
                self.current_smtp_index = (self.current_smtp_index + 1) % len(self.smtp_config)
                
                return True
                
        except smtplib.SMTPAuthenticationError as e:
            print(f"[ERROR] SMTP authentication failed: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            print(f"[ERROR] SMTP error occurred: {str(e)}")
            return False
        except Exception as e:
            print(f"[ERROR] SMTP sending failed: {str(e)}")
            print(f"[DEBUG] Error type: {type(e)}")
            print(f"[DEBUG] Error args: {e.args}")
            return False
            
    def _generate_dkim_signature(self, msg: MIMEMultipart) -> str:
        """Generate DKIM signature for email."""
        try:
            # Implementation of DKIM signature generation
            # This is a placeholder - actual implementation would use the private key
            return f"v=1; a=rsa-sha256; q=dns/txt; c=relaxed/relaxed; d={self.auth_config['dkim_selector']}; s=default"
        except Exception as e:
            print(f"[ERROR] Failed to generate DKIM signature: {str(e)}")
            return ""
            
    def __del__(self):
        """Clean up resources."""
        if hasattr(self, 'proxy_manager'):
            self.proxy_manager.stop_rotation_thread() 