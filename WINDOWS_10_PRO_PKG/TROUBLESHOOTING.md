# COA Analyzer Troubleshooting Guide

## Installation Issues

### 1. Build Process Fails

**Symptoms:**
- Build script stops with an error message
- No Output directory is created
- Missing files after build

**Solutions:**
1. **Administrator Rights**
   - Right-click on `build.bat`
   - Select "Run as administrator"
   - If prompted by UAC, click "Yes"

2. **Internet Connection**
   - Verify your internet connection is working
   - Try accessing the following URLs in a browser:
     - https://www.python.org
     - https://github.com/UB-Mannheim/tesseract/wiki
     - https://aka.ms/vs/17/release/vc_redist.x64.exe

3. **Disk Space**
   - Ensure you have at least 500MB free space
   - Clean up temporary files using Disk Cleanup
   - Delete previous build attempts if they exist

### 2. Installer Fails to Run

**Symptoms:**
- Installer won't start
- Error message about missing dependencies
- Installation process stops midway

**Solutions:**
1. **Missing Dependencies**
   - Run the installer again
   - Allow it to download and install dependencies
   - If manual installation is needed:
     - Python: https://www.python.org/downloads/
     - Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
     - VC++ Redist: https://aka.ms/vs/17/release/vc_redist.x64.exe

2. **Antivirus Interference**
   - Temporarily disable antivirus software
   - Add installer to antivirus exceptions
   - Try running installer again

### 3. Application Won't Start

**Symptoms:**
- Application crashes on startup
- Error message about missing DLLs
- Blank window appears and closes

**Solutions:**
1. **Missing Dependencies**
   - Check if Python is installed correctly
   - Verify Tesseract OCR installation
   - Ensure Visual C++ Redistributable is installed

2. **Environment Variables**
   - Add Tesseract to system PATH:
     1. Open System Properties
     2. Click "Environment Variables"
     3. Add `C:\Program Files\Tesseract-OCR` to PATH
     4. Restart computer

3. **Log Files**
   - Check `%APPDATA%\COA_Analyzer\logs` for error logs
   - Look for specific error messages
   - Contact support with log contents if needed

## Runtime Issues

### 1. PDF Processing Fails

**Symptoms:**
- PDF files won't open
- Error message about PDF processing
- Blank results from PDF files

**Solutions:**
1. **PDF File Issues**
   - Verify PDF is not password protected
   - Check if PDF is scanned (may need OCR)
   - Try converting PDF to text first

2. **Tesseract Configuration**
   - Verify Tesseract installation
   - Check Tesseract data files
   - Reinstall Tesseract if needed

### 2. OCR Issues

**Symptoms:**
- Poor text recognition
- Missing data in results
- Incorrect values extracted

**Solutions:**
1. **Image Quality**
   - Ensure PDF/images are high quality
   - Check for proper contrast
   - Verify text is not rotated

2. **Tesseract Settings**
   - Try different OCR modes
   - Adjust image preprocessing
   - Use specific language packs if needed

### 3. Performance Issues

**Symptoms:**
- Slow processing
- High CPU usage
- Application freezes

**Solutions:**
1. **System Resources**
   - Close other applications
   - Check available RAM
   - Verify CPU usage

2. **File Size**
   - Split large files
   - Optimize PDF/images
   - Use smaller test batches

## Common Error Messages

### "Tesseract not found"
- Solution: Reinstall Tesseract OCR
- Verify installation path
- Check system PATH

### "Missing DLL"
- Solution: Install Visual C++ Redistributable
- Check for conflicting versions
- Reinstall application

### "Python not found"
- Solution: Install Python 3.8 or later
- Verify Python installation
- Check system PATH

## Getting Help

If you're still experiencing issues:

1. **Collect Information**
   - Note exact error messages
   - Save log files
   - Record steps to reproduce

2. **Contact Support**
   - Email: [support email]
   - GitHub: Open an issue
   - Include all collected information

3. **Emergency Workaround**
   - Use command line version
   - Process files individually
   - Export results manually 