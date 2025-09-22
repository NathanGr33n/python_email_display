# 📧 Email Summarizer

A **local, privacy-focused desktop application** that connects to your email inbox via IMAP and generates intelligent summaries of your emails using the TextRank algorithm. All processing happens entirely on your machine—no cloud services, no paid APIs, complete privacy.

![Email Summarizer](https://img.shields.io/badge/Version-1.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Python](https://img.shields.io/badge/Python-3.11+-red)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## ✨ Features

- **🔐 Privacy-First**: All email processing happens locally on your machine
- **📨 IMAP Support**: Secure SSL/TLS connection to any IMAP email server
- **🤖 Local Summarization**: TextRank algorithm generates 2-3 sentence summaries
- **🌙 Dark Theme**: Modern, accessible dark interface with violet accents
- **🔑 Secure Storage**: Credentials stored in system keyring when available
- **🚀 Native Desktop**: Real desktop application with proper window management
- **⚡ Responsive UI**: Non-blocking operations with progress indicators
- **🛡️ No Cloud Dependencies**: Works completely offline (except for IMAP)

## 🎯 Non-negotiables Delivered

✅ **Free + Local-first**: Uses IMAP (Python stdlib) and local TextRank summarization  
✅ **Native GUI**: PySide6-based desktop application with dark theme  
✅ **Single Project**: Everything contained in one repository with MIT license  
✅ **No Paid APIs**: Zero external service dependencies  
✅ **Security**: SSL/TLS IMAP connections, keyring credential storage  

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (tested on 3.11-3.12)
- **IMAP email account** (Gmail, Outlook, Yahoo, etc.)
- **System with keyring support** (recommended for secure credential storage)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd python_email_display
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux  
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python -m app.main
   ```

### First-Time Setup

1. **Launch the app** - You'll see a welcome dialog explaining the features
2. **Configure IMAP settings**:
   - Click "Settings" or accept the welcome prompt
   - Enter your IMAP server details (see [Provider Settings](#-email-provider-settings))
   - Test the connection to verify settings
   - Save settings (stored securely in keyring)
3. **Refresh emails** - Click "Refresh" to fetch and summarize your latest 10 emails

## 📧 Email Provider Settings

### Gmail
```
IMAP Host: imap.gmail.com
Port: 993
SSL/TLS: Enabled
```

**Setup Steps**:
1. Enable 2-factor authentication in your Google account
2. Generate an App Password: [Google Account](https://myaccount.google.com/) → Security → 2-Step Verification → App passwords
3. Use your Gmail address as username and the **App Password** (not your regular password)

### Outlook/Hotmail
```
IMAP Host: outlook.office365.com  
Port: 993
SSL/TLS: Enabled
```

### Yahoo Mail
```
IMAP Host: imap.mail.yahoo.com
Port: 993  
SSL/TLS: Enabled
```

### Other Providers
Most email providers support IMAP. Check your provider's documentation for:
- IMAP server hostname
- Port (usually 993 for SSL)
- Authentication requirements

## 🏢 Project Structure

```
python_email_display/
├─ app/                     # Main application package
│  ├─ __init__.py          # Package initialization
│  ├─ main.py              # Application entry point and startup logic
│  ├─ ui_main.py           # Main window UI and email display cards
│  ├─ ui_settings.py       # Settings dialog and IMAP configuration
│  ├─ imap_client.py       # IMAP connection handling and email fetching
│  ├─ summarizer.py        # Local TextRank-based email summarization
│  ├─ workers.py           # Qt worker threads for background operations
│  ├─ models.py            # Data models (EmailItem, ImapConfig, etc.)
│  ├─ theming.py           # Dark theme styling and color schemes
│  └─ utils.py             # Text processing and utility functions
├─ logs/                   # Application logs (auto-created at runtime)
├─ requirements.txt        # Python dependencies with version constraints
├─ email_summary_gmail.py  # Legacy script (standalone version)
├─ README.md              # This comprehensive documentation
└─ LICENSE               # MIT License
```

## 🔧 Configuration Options

### IMAP Settings
- **Host**: IMAP server hostname
- **Port**: Usually 993 for SSL (143 for non-SSL, not recommended)
- **Username**: Your email address
- **Password**: Account password or app password
- **Folder**: Email folder to read from (default: INBOX)

### Application Preferences
- **Auto-refresh on startup**: Automatically fetch emails when app starts
- **Max emails to fetch**: Number of recent emails to display (1-100)
- **Summary sentences**: Length of generated summaries (1-10 sentences)
- **Connection timeout**: Network timeout in seconds (5-120)

### Credential Storage
- **Keyring (Recommended)**: Secure system keyring storage
- **.env file (Fallback)**: Plain text file storage (less secure)

## 📦 Building Executable

Create a standalone executable that runs without Python installation:

### Using PyInstaller

```bash
# Install PyInstaller (if not already installed)
pip install pyinstaller

# Build executable
pyinstaller email_summarizer.spec

# Find your executable in:
# Windows: dist/EmailSummarizer.exe
# macOS: dist/EmailSummarizer.app  
# Linux: dist/EmailSummarizer
```

### Build Options

**One-file executable**:
```bash
pyinstaller --onefile --windowed --name "EmailSummarizer" app/main.py
```

**One-folder distribution** (faster startup):
```bash
pyinstaller --onedir --windowed --name "EmailSummarizer" app/main.py
```

## 🛠️ Development

### Running in Development
```bash
# With verbose logging
python -m app.main --log-level DEBUG

# Direct module execution
python app/main.py
```

### Code Organization
- **UI Components**: `ui_main.py`, `ui_settings.py` 
- **Business Logic**: `imap_client.py`, `summarizer.py`
- **Threading**: `workers.py` (keeps UI responsive)
- **Data Models**: `models.py` (EmailItem, Settings)
- **Utilities**: `utils.py`, `theming.py`

### Adding Features
The codebase is modular and well-documented. Key extension points:
- **Email Actions**: Extend `EmailCard` click handlers
- **Summarization**: Modify `LocalSummarizer` for different algorithms
- **Themes**: Extend `theming.py` for additional color schemes
- **Providers**: Add provider-specific handling in `imap_client.py`

### Testing & Quality Assurance

```bash
# Run the application in debug mode
python -m app.main --log-level DEBUG

# Test IMAP connectivity independently
python -c "from app.imap_client import ImapClient; # ... test code"

# Check dependencies and versions
pip list | grep -E '(PySide6|sumy|keyring)'

# Validate requirements
pip check
```

### Performance Considerations

- **Memory Usage**: Email content is processed in streaming fashion
- **Network Efficiency**: Only fetches recent emails, supports connection pooling
- **UI Responsiveness**: All blocking operations run in background threads
- **Startup Time**: Lazy loading of heavy dependencies

## 🐛 Troubleshooting

### Common Issues

**"Authentication failed"**
- Verify IMAP credentials are correct
- For Gmail: Ensure you're using an App Password, not your regular password
- Check if 2-factor authentication is required
- Verify IMAP is enabled in your email provider settings

**"Connection failed"** 
- Check internet connection
- Verify IMAP host and port are correct
- Try disabling firewall/antivirus temporarily
- Some corporate networks block IMAP ports

**"Missing dependencies"**
```bash
pip install -r requirements.txt
```

**"SSL Certificate errors"**
- Usually indicates incorrect IMAP settings
- Verify the hostname is exactly correct
- Some providers require specific SSL/TLS settings

**"No emails found"**
- Check that the folder name is correct (usually "INBOX")
- Verify there are actually emails in the specified folder
- Some providers use different folder names

**"Summary generation failed"**
- Check that emails contain readable text content
- HTML-only emails are converted to text automatically
- Very short emails may not generate meaningful summaries

### Debugging

**Enable verbose logging**:
```bash
python -m app.main --log-level DEBUG
```

**Check log files**:
- Logs are saved to `logs/email_summarizer.log`
- Contains detailed information about errors and operations

**Test IMAP connection manually**:
```python
from app.imap_client import ImapClient
from app.models import ImapConfig

config = ImapConfig(
    host="imap.gmail.com",
    username="your.email@gmail.com", 
    password="your_app_password"
)

client = ImapClient(config)
success, message = client.test_connection()
print(f"Success: {success}, Message: {message}")
```

## 🔒 Privacy & Security

### Data Handling
- **No telemetry**: Application doesn't send any usage data
- **Local processing**: All email content stays on your machine  
- **Secure connections**: IMAP over SSL/TLS only
- **Credential security**: System keyring storage preferred

### What Data is Stored
- **IMAP settings**: Server, port, username (in keyring or .env)
- **Email content**: Temporarily in memory during processing only
- **Summaries**: Generated summaries are not persistently stored
- **Logs**: Basic operation logs (no sensitive data logged)

### Network Connections
The application only makes network connections to:
1. **Your IMAP server** (for fetching emails)

No other external services are contacted.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions from developers of all experience levels! This project follows standard open-source practices and maintains high code quality standards.

### Development Workflow

1. **Fork & Clone**
   ```bash
   git clone https://github.com/yourusername/python_email_display.git
   cd python_email_display
   ```

2. **Environment Setup**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

3. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Your Changes**
   - Follow existing code patterns and style
   - Add type hints to new functions
   - Update docstrings for public methods
   - Test your changes thoroughly

5. **Test & Validate**
   ```bash
   # Run the application
   python -m app.main
   
   # Check for import errors
   python -c "import app; print('Import successful')"
   ```

6. **Commit & Push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

7. **Submit Pull Request**
   - Provide clear description of changes
   - Reference any related issues
   - Include screenshots for UI changes

### Contribution Guidelines

- **Code Style**: Follow PEP 8 and existing patterns
- **Type Hints**: Add type annotations to new code
- **Documentation**: Update docstrings and README as needed
- **Backwards Compatibility**: Maintain compatibility when possible
- **Security**: Never commit secrets or credentials

### Areas for Contribution

- **Email Provider Support**: Add configurations for more IMAP providers
- **Summarization Algorithms**: Implement alternative summarization methods
- **UI Enhancements**: Improve accessibility and user experience
- **Performance Optimization**: Reduce memory usage or improve speed
- **Cross-platform Testing**: Verify compatibility across OS platforms
- **Documentation**: Improve setup guides and troubleshooting docs

## 📚 Technical Details

### Dependencies
- **PySide6**: Qt-based GUI framework
- **sumy**: TextRank text summarization
- **beautifulsoup4**: HTML parsing for email content
- **python-dateutil**: Date parsing utilities
- **keyring**: Secure credential storage
- **python-dotenv**: Environment variable management
- **pyinstaller**: Executable building

### Architecture
- **MVC Pattern**: Clear separation of UI, business logic, and data
- **Threading**: Background workers prevent UI blocking
- **Signal/Slots**: Qt-based event handling for responsive UI
- **Modular Design**: Easy to extend and modify

### Performance
- **Efficient IMAP**: Fetches only recent emails, not entire inbox
- **Lazy Loading**: Summaries generated on-demand  
- **Memory Management**: Emails processed in batches
- **Responsive UI**: All network operations in background threads

---

**Made with ❤️ for privacy-conscious developers and email users**

*A comprehensive, local-first email summarization solution that respects your privacy while keeping you informed.*

## 🚨 Requirements

- **Python 3.11+** - Leverages modern Python features and type hints
- **IMAP-enabled email account** - Gmail, Outlook, Yahoo Mail, or any IMAP provider
- **Desktop environment** - Windows, macOS, or Linux with GUI support
- **Network access** - For IMAP connections (local processing only)

## 🔄 Recent Updates

- **Enhanced UI/UX** - Modern dark theme with improved accessibility
- **Robust Error Handling** - Comprehensive error recovery and user feedback
- **Secure Credential Management** - System keyring integration with fallback options
- **Multi-threaded Architecture** - Non-blocking UI with background email processing
- **Cross-platform Compatibility** - Tested on Windows, macOS, and Linux

## 🎓 For Developers

This project demonstrates several software engineering best practices:

- **Clean Architecture** - Separation of concerns with clear module boundaries
- **Async/Threading** - Responsive UI through background worker threads
- **Security First** - Secure credential storage and encrypted connections
- **Error Resilience** - Graceful degradation and comprehensive error handling
- **Cross-platform Design** - Consistent experience across operating systems
- **Privacy by Design** - No external dependencies for core functionality

### Code Quality Features

- **Type Hints** - Full type annotation for better IDE support and code clarity
- **Modular Design** - Easy to extend, test, and maintain
- **Comprehensive Logging** - Debug-friendly logging throughout the application
- **Configuration Management** - Flexible settings with secure defaults
- **Resource Management** - Proper cleanup of network connections and threads

## 🗺️ Roadmap

### Planned Features

- [ ] **Email Search & Filtering** - Full-text search within email summaries
- [ ] **Multiple Account Support** - Manage multiple IMAP accounts simultaneously
- [ ] **Custom Summarization** - User-configurable summary length and style
- [ ] **Email Templates** - Quick actions for common email responses
- [ ] **Notification System** - Desktop notifications for new emails
- [ ] **Export Functionality** - Export summaries to various formats (PDF, CSV)
- [ ] **Advanced Theming** - Light theme and custom color schemes
- [ ] **Plugin Architecture** - Extensible system for custom email processors

### Technical Improvements

- [ ] **Unit Testing** - Comprehensive test suite for all modules
- [ ] **CI/CD Pipeline** - Automated testing and building
- [ ] **Performance Profiling** - Memory and CPU usage optimization
- [ ] **Accessibility** - Enhanced screen reader and keyboard navigation support
- [ ] **Internationalization** - Multi-language support

## 📈 Changelog

### v1.0.0 - Initial Release
- ✅ **Core IMAP Integration** - Secure SSL/TLS email fetching
- ✅ **Local Summarization** - TextRank-based email summaries
- ✅ **Modern Dark UI** - PySide6-based desktop interface
- ✅ **Secure Credential Storage** - System keyring integration
- ✅ **Cross-platform Support** - Windows, macOS, and Linux compatibility
- ✅ **Background Processing** - Non-blocking UI with worker threads
- ✅ **Comprehensive Logging** - Debug-friendly error tracking
- ✅ **PyInstaller Support** - Standalone executable generation

