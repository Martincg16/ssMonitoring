# AWS SES Setup for Solar Monitoring Email Alerts

This guide explains how to configure AWS Simple Email Service (SES) for sending email alerts from the Solar Monitoring application.

## 🎯 **Quick Setup Overview**

1. **Verify email addresses** in AWS SES
2. **Create SMTP credentials** 
3. **Configure environment variables**
4. **Test email functionality**

---

## 📧 **Step 1: AWS SES Console Setup**

### **1.1 Access AWS SES**
1. Go to [AWS SES Console](https://console.aws.amazon.com/ses/)
2. Make sure you're in the **US East 1 (N. Virginia)** region (or your preferred region)

### **1.2 Verify Email Addresses**
1. In SES Console, go to **Verified identities**
2. Click **Create identity**
3. Select **Email address**
4. Enter the email you want to **send FROM**: `alerts@yourdomain.com`
5. Click **Create identity**
6. **Check your email** and click the verification link

**Repeat for recipient emails:**
- Add each email address that will **receive** alerts
- Each recipient must verify their email address

> ⚠️ **Important**: In SES Sandbox mode, you can only send emails to verified addresses

---

## 🔑 **Step 2: Create SMTP Credentials**

### **2.1 Generate SMTP Credentials**
1. In SES Console, go to **SMTP settings**
2. Click **Create SMTP credentials**
3. Enter username: `solar-monitoring-smtp`
4. Click **Create user**
5. **Download the credentials** - you'll need them for environment variables

### **2.2 Note Your SMTP Endpoint**
- **US East 1**: `email-smtp.us-east-1.amazonaws.com`
- **EU West 1**: `email-smtp.eu-west-1.amazonaws.com`
- **Other regions**: Check the SES console for your region's SMTP endpoint

---

## 🌍 **Step 3: Configure Environment Variables**

### **3.1 Update Your .env File**
```bash
# AWS SES SMTP Credentials
AWS_SES_SMTP_USER=your_actual_smtp_username
AWS_SES_SMTP_PASSWORD=your_actual_smtp_password

# Email Alert Settings
ALERT_FROM_EMAIL=alerts@yourdomain.com
ALERT_EMAIL_RECIPIENTS=admin@yourdomain.com,tech@yourdomain.com
```

### **3.2 For Production (EC2)**
Add these to your deployment environment:
```bash
export AWS_SES_SMTP_USER="your_actual_smtp_username"
export AWS_SES_SMTP_PASSWORD="your_actual_smtp_password"
export ALERT_FROM_EMAIL="alerts@yourdomain.com"
export ALERT_EMAIL_RECIPIENTS="admin@yourdomain.com,tech@yourdomain.com"
```

---

## 🧪 **Step 4: Test Email Functionality**

### **4.1 Test with Management Command**
```bash
# Test ERROR level alerts
python manage.py test_email_alerts --level error

# Test CRITICAL level alerts  
python manage.py test_email_alerts --level critical
```

### **4.2 Test with Manual Log**
```python
import logging
logger = logging.getLogger('management_commands')
logger.error("Test error message")
logger.critical("Test critical message")
```

---

## 📈 **Step 5: Move Out of Sandbox (Production)**

### **5.1 Request Production Access**
1. In SES Console, go to **Sending statistics**
2. Click **Request production access**
3. Fill out the form:
   - **Use case**: Application monitoring alerts
   - **Expected sending volume**: ~50 emails/month
   - **Bounce/complaint handling**: Automatic

### **5.2 Production Benefits**
- ✅ Send to **any email address** (not just verified ones)
- ✅ Higher sending limits
- ✅ Better deliverability

---

## 🔧 **Troubleshooting**

### **Common Issues**

**1. "Email not received"**
- ✅ Check spam/junk folders
- ✅ Verify recipient email in SES console
- ✅ Check SES sending statistics for bounces

**2. "SMTP Authentication Failed"**
- ✅ Double-check SMTP username/password
- ✅ Ensure credentials are for the correct AWS region
- ✅ Verify environment variables are loaded

**3. "Sender email not verified"**
- ✅ Verify the `ALERT_FROM_EMAIL` in SES console
- ✅ Check verification status in Verified identities

**4. "Daily sending quota exceeded"**
- ✅ Check SES sending limits in console
- ✅ Request limit increase if needed
- ✅ Consider moving out of sandbox mode

### **Debug Commands**
```bash
# Check if environment variables are loaded
echo $AWS_SES_SMTP_USER
echo $ALERT_EMAIL_RECIPIENTS

# Test Django email configuration
python manage.py shell
>>> from django.conf import settings
>>> print(settings.EMAIL_HOST_USER)
>>> print(settings.ALERT_EMAIL_RECIPIENTS)
```

---

## 💰 **Cost Information**

**AWS SES Pricing:**
- ✅ **62,000 emails per month FREE** when sending from EC2
- ✅ $0.10 per 1,000 emails after free tier
- ✅ Very cost-effective for monitoring alerts

**Expected Usage:**
- ~10-50 emails per month (only for errors/critical issues)
- Well within free tier limits

---

## 🛡️ **Security Best Practices**

1. **Never commit credentials** to git
2. **Use environment variables** for all sensitive data
3. **Rotate SMTP credentials** regularly
4. **Monitor SES sending statistics** for unusual activity
5. **Use specific FROM addresses** (not generic gmail accounts)

---

## 📝 **Email Alert Examples**

When configured correctly, you'll receive emails like:

**Subject:** `🚨 Solar Monitoring Alert - URGENT: CRITICAL`

**Body:**
```
🔴 Solar Monitoring System Alert

⏰ Time: 2025-01-15 14:30:22 (Colombian Time)
🔖 Level: CRITICAL
🏗️ Component: Huawei Data Fetcher
📍 Logger: huawei_fetcher

📝 Message:
|HuaweiFetcher|login| API authentication failed after 3 retries

🔍 Technical Details:
File: /opt/solar-monitoring/ssMonitoringProjectDJ/solarDataFetch/fetchers/huaweiFetcher.py
Function: login
Line: 45

🛠️ Next Steps:
1. Check the application logs for more context
2. Verify API connectivity and credentials
3. Check system resources (disk space, memory)
4. Review recent deployments or configuration changes
```

Perfect for immediate notification of critical issues! 🚨 