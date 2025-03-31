# MadCat Mailer

A powerful email sending tool with support for multiple SMTP servers, templates, and advanced features.

## Features

- Multiple SMTP server support
- HTML and text email templates
- Attachment support
- Proxy support
- Rate limiting and throttling
- Detailed logging
- IPv4/IPv6 support
- Blacklist checking
- Read receipt handling
- Custom headers support

## Requirements

- Python 3.9 or higher
- Required packages (install via `pip install -r requirements.txt`):
  - psutil
  - dnspython
  - requests
  - pyOpenSSL

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mass-mailer.git
cd mass-mailer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the dummy config file:
```bash
cp dummy.config your_config.config
```

2. Edit your_config.config with your SMTP settings and other parameters.

## Usage

Run the script with your configuration file:
```bash
python3 madcatmailer.py your_config.config
```

## Configuration File Format

The configuration file should contain the following sections:
- [smtp] - SMTP server settings
- [email] - Email content settings
- [proxy] - Proxy settings (optional)
- [advanced] - Advanced settings

See dummy.config for a complete example.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Made by Aels for the security community
- Forum: https://xss.is
- GitHub: https://github.com/aels/mailtools
- Telegram: https://t.me/IamLavander
