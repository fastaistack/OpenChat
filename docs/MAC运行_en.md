#  About OpenChat Security and macOS System Settings

Thank you for using **OpenChat**!

OpenChat is an open-source, locally-deployable AI desktop application designed to provide developers and professionals with a **secure, free, and controllable AI platform**.

---

## 🔐 We Take Your Privacy and Data Security Seriously

- ✅ **Open-source & Transparent**: You can fully review and verify the source code on our GitHub repository  
- ✅ **Offline Capable**: OpenChat **does not collect any user data**, has no tracking, and does not sync to the cloud  
- ✅ **Data Stored Locally**: All chat records, settings, and model interactions stay entirely on your device—you have full control

---

## ❗ Why Does macOS Show “Cannot Open” or “App is Damaged”?

Since OpenChat is built and packaged directly by the development team (and not officially notarized via the App Store), macOS security mechanisms (Gatekeeper) may display the following alerts when you first launch it:

- “OpenChatInstall cannot be opened because the developer cannot be verified”
- “The file is damaged and should be moved to the Trash”
- “App from an unidentified developer”

These messages do **not** mean the software is dangerous. It’s simply how macOS handles all unsigned apps by default.

---

## ✅ How to Fix This: Enable the “Allow Apps from Anywhere” Option

<br>

1. Open **System Settings** or **System Preferences**  
2. Go to **Security & Privacy** and scroll down to the **Security** section  
3. Look for **“Allow apps downloaded from:”**  
4. Select ✅ **“Anywhere”**

<br>

If you do **not see the “Anywhere”** option, macOS has hidden it by default. Please follow the steps below to make it visible and run OpenChat properly:

---

### 📦 Step 1: Open the Terminal

Go to Launchpad → Others → **Terminal**,  
or press `⌘ + Space` and type “Terminal”

---

### 📋 Step 2: Enter the following command and press Enter

```bash
sudo spctl --master-disable
```

The system will prompt for your Mac login password (nothing will show as you type). Press Enter after entering your password.

---

### 🧭 Step 3: Confirm the “Anywhere” Option Appears

Once enabled, go to **System Settings > Security & Privacy > Security**  
Under **“Allow apps downloaded from:”**, the **“Anywhere”** option should now appear.

> If you still don’t see it, please restart your Mac and check again.

---

## 🔐 Optional: Re-enable macOS Default Security

If you want to restore macOS default protections after installing OpenChat, just run:

```bash
sudo spctl --master-enable
```

This will hide the “Anywhere” option and re-enable full Gatekeeper protections.

---

<br>
<br>

Thank you for your trust and support. We hope you enjoy using OpenChat!

— The OpenChat Development Team
